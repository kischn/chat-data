"""AI Chat service for natural language data analysis."""
import re
from typing import Any
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Conversation, Message, Dataset, DatasetColumn
from app.schemas import ChatRequest, ChatResponse


class AIChatService:
    """Service for AI-powered data analysis conversations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.ai.api_key,
            base_url=settings.ai.base_url,
        )
        self.model = settings.ai.model
        self.temperature = settings.ai.temperature

    async def create_conversation(
        self,
        user_id: UUID,
        dataset_id: UUID | None = None,
        title: str | None = None,
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            dataset_id=dataset_id,
            title=title or "New Analysis",
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation | None:
        """Get a conversation by ID."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def chat(
        self,
        conversation_id: UUID,
        request: ChatRequest,
        user_id: UUID,
    ) -> Message:
        """Process a chat message and return AI response."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found")

        # Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )
        self.db.add(user_message)
        await self.db.flush()

        # Build context
        context = await self._build_context(conversation)

        # Get conversation history
        history = await self._get_history(conversation_id)

        # Generate response
        response_content, code_result = await self._generate_response(
            user_message=request.message,
            context=context,
            history=history,
            execute_code=request.code_execution,
            conversation_id=conversation_id,
        )

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response_content,
            code_result=code_result,
        )
        self.db.add(assistant_message)
        await self.db.commit()
        await self.db.refresh(assistant_message)

        return assistant_message

    async def _build_context(self, conversation: Conversation) -> dict[str, Any]:
        """Build context for the AI from dataset metadata."""
        from sqlalchemy import select

        if not conversation.dataset_id:
            return {"has_dataset": False}

        result = await self.db.execute(
            select(Dataset).where(Dataset.id == conversation.dataset_id)
        )
        dataset = result.scalar_one_or_none()

        if not dataset:
            return {"has_dataset": False}

        result = await self.db.execute(
            select(DatasetColumn)
            .where(DatasetColumn.dataset_id == conversation.dataset_id)
            .order_by(DatasetColumn.position)
        )
        columns = result.scalars().all()

        column_details = []
        for col in columns:
            stats = col.statistics or {}
            column_details.append({
                "name": col.name,
                "type": col.data_type,
                "nullable": col.nullable,
                "statistics": stats,
            })

        return {
            "has_dataset": True,
            "dataset_id": str(conversation.dataset_id),
            "dataset_name": dataset.name,
            "dataset_description": dataset.description,
            "row_count": dataset.metadata.get("row_count") if dataset.metadata else None,
            "columns": column_details,
        }

    async def _get_history(self, conversation_id: UUID) -> list[dict]:
        """Get conversation history for context."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def _generate_response(
        self,
        user_message: str,
        context: dict[str, Any],
        history: list[dict],
        execute_code: bool = True,
        conversation_id: UUID | None = None,
    ) -> tuple[str, dict[str, Any] | None]:
        """Generate AI response using LLM."""
        # Build enhanced prompt for code generation
        system_prompt = self._build_system_prompt(context, execute_code)

        messages = [{"role": "system", "content": system_prompt}] + history + [
            {"role": "user", "content": user_message}
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )

        response_content = response.choices[0].message.content or ""

        # Extract and execute code if requested
        code_result = None
        if execute_code and "```python" in response_content:
            code = self._extract_code(response_content)
            if code and context.get("has_dataset"):
                from app.services import CodeExecutor
                executor = CodeExecutor(self.db)
                try:
                    code_result = await executor.execute(
                        code=code,
                        dataset_id=UUID(context["dataset_id"]),
                        conversation_id=conversation_id,
                    )
                    # Append result to response
                    if code_result.get("success"):
                        response_content += self._format_code_result(code_result)
                except Exception as e:
                    response_content += f"\n\n*Code execution error: {str(e)}*"

        return response_content, code_result

    def _extract_code(self, content: str) -> str | None:
        """Extract Python code from markdown response."""
        pattern = r"```python\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL)
        return matches[0] if matches else None

    def _format_code_result(self, result: dict[str, Any]) -> str:
        """Format code execution result."""
        parts = ["\n\n**Analysis Results:**"]

        if result.get("dataframe_info"):
            info = result["dataframe_info"]
            parts.append(f"- Data shape: {info['shape'][0]} rows x {info['shape'][1]} columns")
            parts.append(f"- Columns: {', '.join(info['columns'][:5])}")
            if len(info['columns']) > 5:
                parts.append(f"  ... and {len(info['columns']) - 5} more")

        if result.get("charts"):
            parts.append("\n**Visualizations:**")
            for chart in result["charts"]:
                parts.append(f"- Chart generated: {chart['type']}")

        if result.get("output"):
            parts.append(f"\n```\n{result['output']}\n```")

        return "\n".join(parts)

    def _build_system_prompt(self, context: dict[str, Any], execute_code: bool) -> str:
        """Build system prompt for the AI assistant."""
        prompt = """You are an expert data analysis assistant. Your role is to help users explore, clean, analyze, and visualize their datasets through natural conversation.

## Your Capabilities
1. Explore data distributions and statistics
2. Clean and preprocess data
3. Generate visualizations
4. Perform statistical analysis
5. Build predictive models

## Response Format
- Start with a brief explanation
- Provide Python code in ```python blocks when analysis requires computation
- Explain the code before showing it
- Summarize key findings at the end

## Code Guidelines (when generating Python)
- Use pandas for data manipulation
- Use matplotlib for visualizations
- Save charts to the output directory using plt.savefig()
- Use clean, readable variable names
- Add comments for complex logic

"""

        if execute_code:
            prompt += """
## Code Execution
Your code will be executed automatically. Follow these rules:
1. Load data using: df = pd.read_csv(dataset_path)
2. For visualizations: plt.savefig(f"{output_dir}/chart_{conversation_id}_{i}.png")
3. Use 'conversation_id' variable for chart naming
4. Always use English variable names
5. Keep code concise and focused

"""

        if context.get("has_dataset"):
            prompt += f"\n## Current Dataset Context\n"
            prompt += f"- Dataset ID: {context['dataset_id']}\n"
            prompt += f"- Dataset: {context['dataset_name']}\n"
            if context.get("dataset_description"):
                prompt += f"- Description: {context['dataset_description']}\n"
            if context.get("row_count"):
                prompt += f"- Rows: {context['row_count']}\n"

            prompt += "\n## Column Details\n"
            for col in context.get("columns", []):
                stats = col.get("statistics", {}) or {}
                prompt += f"\n### {col['name']} ({col['type']})\n"
                if stats.get("null_rate"):
                    prompt += f"- Missing: {stats['null_rate']:.1%}\n"
                if stats.get("unique_count"):
                    prompt += f"- Unique values: {stats['unique_count']}\n"
                if stats.get("mean") is not None:
                    prompt += f"- Mean: {stats['mean']:.2f}, Std: {stats.get('std', 0):.2f}\n"
                if stats.get("min") is not None:
                    prompt += f"- Range: [{stats['min']:.2f}, {stats['max']:.2f}]\n"

        prompt += "\n\nUser's message: "
        return prompt

    async def get_conversations_by_dataset(
        self,
        user_id: UUID,
        dataset_id: UUID,
    ) -> list[Conversation]:
        """Get all conversations for a dataset."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.dataset_id == dataset_id,
            )
            .order_by(Conversation.updated_at.desc())
        )
        return result.scalars().all()
