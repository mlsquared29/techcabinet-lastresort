from celery import shared_task, group
from .models import PSAGroup, PSAEntry, AIResponse

@shared_task
def generate_single_ai_response(psa_group_id, psa_entry_id):
    """Generate a single AI response for a PSA entry"""
    try:
        psa_entry = PSAEntry.objects.get(id=psa_entry_id, group_id=psa_group_id)
        
        ai_solution, ai_answer = psa_entry.get_ai_solution_and_answer()
        
        ai_response = AIResponse.objects.create(
            psa_entry=psa_entry,
            ai_solution=ai_solution,
            ai_answer=ai_answer
        )
        
        return {
            'ai_response_id': ai_response.id,
            'psa_entry_id': psa_entry_id,
            'success': True
        }
    except Exception as e:
        print(f"Error generating AI response for PSA entry {psa_entry_id}: {e}")
        return {
            'psa_entry_id': psa_entry_id,
            'success': False,
            'error': str(e)
        }

@shared_task
def generate_ai_responses(psa_group_id):
    """Generate AI responses for all PSA entries in a group"""
    try:
        psa_group = PSAGroup.objects.get(id=psa_group_id)
        psa_entries = psa_group.psaentry_set.all()
        
        job = group(generate_single_ai_response.s(psa_group_id, entry.id) for entry in psa_entries)
        result = job.apply_async()
        
        return result.id
    except Exception as e:
        print(f"Error setting up parallel tasks for PSA group {psa_group_id}: {e}")
        return None