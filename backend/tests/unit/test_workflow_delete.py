import pytest
from services.workflow_repository import WorkflowRepository
from models.workflow import WorkflowState


@pytest.mark.asyncio
async def test_workflow_repository_delete():
    repo = WorkflowRepository()
    state = WorkflowState(
        workflow_id="wf-test-delete-123",
        query="Test query for delete",
        status="planned"
    )
    
    await repo.save_workflow(state)
    fetched = await repo.get_workflow("wf-test-delete-123")
    assert fetched is not None
    assert fetched.workflow_id == "wf-test-delete-123"

    # Delete
    deleted = await repo.delete_workflow("wf-test-delete-123")
    assert deleted is True

    # Verify not found
    after_delete = await repo.get_workflow("wf-test-delete-123")
    assert after_delete is None

    # Delete non-existent returns False
    deleted_again = await repo.delete_workflow("wf-test-delete-123")
    assert deleted_again is False
