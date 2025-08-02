from celery import shared_task, group
from .models import Query, Output

@shared_task
def generate_single_output(query_id, output_index):
    """Generate a single output for a query"""
    try:
        query = Query.objects.get(id=query_id)
        output_text = query.get_output()
        output = query.output_set.create(output=output_text)
        return {
            'output_id': output.id,
            'output_index': output_index,
            'success': True
        }
    except Exception as e:
        print(f"Error generating output {output_index} for query {query_id}: {e}")
        return {
            'output_index': output_index,
            'success': False,
            'error': str(e)
        }

@shared_task
def generate_outputs_for_query(query_id):
    """Generate multiple outputs in parallel for a query"""
    try:
        query = Query.objects.get(id=query_id)
        amount = query.amount
        
        # Create a group of tasks to run in parallel
        job = group(generate_single_output.s(query_id, i) for i in range(amount))
        result = job.apply_async()
        
        return result.id
    except Exception as e:
        print(f"Error setting up parallel tasks for query {query_id}: {e}")
        return None