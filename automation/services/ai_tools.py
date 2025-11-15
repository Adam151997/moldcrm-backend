"""
AI Agent Tools - Functions that the Gemini AI Agent can call
Each function must have:
1. Type hints for all parameters
2. Detailed docstrings describing purpose, args, and returns
3. Error handling
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, date
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone


def get_lead(lead_id: int, account_id: int) -> Dict[str, Any]:
    """
    Retrieve detailed information about a specific lead.

    Args:
        lead_id: The unique identifier of the lead
        account_id: The account ID to verify permissions

    Returns:
        Dictionary containing lead details including name, email, company, status, and notes
    """
    try:
        from crm.models import Lead
        lead = Lead.objects.get(id=lead_id, account_id=account_id)
        return {
            "success": True,
            "lead": {
                "id": lead.id,
                "name": f"{lead.first_name} {lead.last_name}",
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "email": lead.email,
                "phone": lead.phone,
                "company": lead.company,
                "status": lead.status,
                "source": lead.source,
                "notes": lead.notes,
                "created_at": lead.created_at.isoformat(),
                "assigned_to": lead.assigned_to.get_full_name() if lead.assigned_to else None
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to retrieve lead: {str(e)}"
        }


def get_deal(deal_id: int, account_id: int) -> Dict[str, Any]:
    """
    Retrieve detailed information about a specific deal.

    Args:
        deal_id: The unique identifier of the deal
        account_id: The account ID to verify permissions

    Returns:
        Dictionary containing deal details including name, amount, stage, contact, and probability
    """
    try:
        from crm.models import Deal
        deal = Deal.objects.get(id=deal_id, account_id=account_id)
        return {
            "success": True,
            "deal": {
                "id": deal.id,
                "name": deal.name,
                "amount": float(deal.amount) if deal.amount else 0,
                "stage": deal.stage,
                "pipeline_stage": deal.pipeline_stage.display_name if deal.pipeline_stage else None,
                "probability": deal.probability,
                "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
                "contact_name": f"{deal.contact.first_name} {deal.contact.last_name}",
                "contact_email": deal.contact.email,
                "contact_company": deal.contact.company,
                "created_at": deal.created_at.isoformat(),
                "assigned_to": deal.assigned_to.get_full_name() if deal.assigned_to else None
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to retrieve deal: {str(e)}"
        }


def get_contact(contact_id: int, account_id: int) -> Dict[str, Any]:
    """
    Retrieve detailed information about a specific contact.

    Args:
        contact_id: The unique identifier of the contact
        account_id: The account ID to verify permissions

    Returns:
        Dictionary containing contact details including name, email, company, title, and associated deals
    """
    try:
        from crm.models import Contact
        contact = Contact.objects.get(id=contact_id, account_id=account_id)
        deals = contact.deals.all()
        return {
            "success": True,
            "contact": {
                "id": contact.id,
                "name": f"{contact.first_name} {contact.last_name}",
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email": contact.email,
                "phone": contact.phone,
                "company": contact.company,
                "title": contact.title,
                "department": contact.department,
                "deals_count": deals.count(),
                "created_at": contact.created_at.isoformat()
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to retrieve contact: {str(e)}"
        }


def create_lead(first_name: str, last_name: str, email: str, account_id: int, user_id: int,
                company: str = "", phone: str = "", source: str = "", notes: str = "") -> Dict[str, Any]:
    """
    Create a new lead in the CRM system.

    Args:
        first_name: Lead's first name
        last_name: Lead's last name
        email: Lead's email address
        account_id: The account ID creating this lead
        user_id: The user ID creating this lead
        company: Lead's company name (optional)
        phone: Lead's phone number (optional)
        source: How the lead was acquired (optional)
        notes: Additional notes about the lead (optional)

    Returns:
        Dictionary with success status and created lead ID
    """
    try:
        from crm.models import Lead
        from users.models import User

        user = User.objects.get(id=user_id, account_id=account_id)
        lead = Lead.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            company=company,
            phone=phone,
            source=source,
            notes=notes,
            account_id=account_id,
            created_by=user,
            assigned_to=user,
            status='new'
        )
        return {
            "success": True,
            "lead_id": lead.id,
            "message": f"Lead '{first_name} {last_name}' created successfully with ID {lead.id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create lead: {str(e)}"
        }


def create_deal(name: str, contact_id: int, account_id: int, user_id: int,
                amount: float = 0, probability: int = 50,
                expected_close_date: Optional[str] = None, notes: str = "") -> Dict[str, Any]:
    """
    Create a new deal in the CRM system.

    Args:
        name: Deal name/title
        contact_id: ID of the contact associated with this deal
        account_id: The account ID creating this deal
        user_id: The user ID creating this deal
        amount: Deal amount in dollars (optional, default 0)
        probability: Probability of closing (0-100, optional, default 50)
        expected_close_date: Expected close date in ISO format YYYY-MM-DD (optional)
        notes: Additional notes about the deal (optional)

    Returns:
        Dictionary with success status and created deal ID
    """
    try:
        from crm.models import Deal, Contact
        from users.models import User

        user = User.objects.get(id=user_id, account_id=account_id)
        contact = Contact.objects.get(id=contact_id, account_id=account_id)

        deal_data = {
            "name": name,
            "contact": contact,
            "account_id": account_id,
            "created_by": user,
            "assigned_to": user,
            "amount": Decimal(str(amount)),
            "probability": probability,
            "stage": 'prospect'
        }

        if expected_close_date:
            deal_data["expected_close_date"] = datetime.fromisoformat(expected_close_date).date()

        deal = Deal.objects.create(**deal_data)

        return {
            "success": True,
            "deal_id": deal.id,
            "message": f"Deal '{name}' created successfully with ID {deal.id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create deal: {str(e)}"
        }


def update_lead_status(lead_id: int, new_status: str, account_id: int) -> Dict[str, Any]:
    """
    Update the status of an existing lead.

    Args:
        lead_id: The unique identifier of the lead to update
        new_status: New status value (must be one of: 'new', 'contacted', 'qualified', 'unqualified')
        account_id: The account ID to verify permissions

    Returns:
        Dictionary with success status and updated lead information
    """
    try:
        from crm.models import Lead

        valid_statuses = ['new', 'contacted', 'qualified', 'unqualified']
        if new_status not in valid_statuses:
            return {
                "success": False,
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            }

        lead = Lead.objects.get(id=lead_id, account_id=account_id)
        old_status = lead.status
        lead.status = new_status
        lead.save()

        return {
            "success": True,
            "message": f"Lead status updated from '{old_status}' to '{new_status}'",
            "lead_id": lead.id,
            "lead_name": f"{lead.first_name} {lead.last_name}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update lead status: {str(e)}"
        }


def update_deal_stage(deal_id: int, new_stage: str, account_id: int) -> Dict[str, Any]:
    """
    Update the stage of an existing deal.

    Args:
        deal_id: The unique identifier of the deal to update
        new_stage: New stage value (must be one of: 'prospect', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost')
        account_id: The account ID to verify permissions

    Returns:
        Dictionary with success status and updated deal information
    """
    try:
        from crm.models import Deal

        valid_stages = ['prospect', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
        if new_stage not in valid_stages:
            return {
                "success": False,
                "error": f"Invalid stage. Must be one of: {', '.join(valid_stages)}"
            }

        deal = Deal.objects.get(id=deal_id, account_id=account_id)
        old_stage = deal.stage
        deal.stage = new_stage
        deal.save()

        return {
            "success": True,
            "message": f"Deal stage updated from '{old_stage}' to '{new_stage}'",
            "deal_id": deal.id,
            "deal_name": deal.name
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update deal stage: {str(e)}"
        }


def get_pipeline_summary(account_id: int) -> Dict[str, Any]:
    """
    Get a comprehensive summary of the sales pipeline including deal counts and values by stage.

    Args:
        account_id: The account ID to get pipeline data for

    Returns:
        Dictionary containing pipeline statistics by stage, total value, and deal counts
    """
    try:
        from crm.models import Deal

        deals = Deal.objects.filter(account_id=account_id)

        # Overall stats
        total_deals = deals.count()
        total_value = deals.aggregate(total=Sum('amount'))['total'] or 0
        avg_deal_size = deals.aggregate(avg=Avg('amount'))['avg'] or 0

        # By stage
        stage_breakdown = deals.values('stage').annotate(
            count=Count('id'),
            total_value=Sum('amount')
        ).order_by('stage')

        # Active vs closed
        active_deals = deals.exclude(stage__in=['closed_won', 'closed_lost']).count()
        won_deals = deals.filter(stage='closed_won').count()
        lost_deals = deals.filter(stage='closed_lost').count()

        return {
            "success": True,
            "pipeline": {
                "total_deals": total_deals,
                "total_value": float(total_value),
                "average_deal_size": float(avg_deal_size),
                "active_deals": active_deals,
                "won_deals": won_deals,
                "lost_deals": lost_deals,
                "stage_breakdown": [
                    {
                        "stage": item['stage'],
                        "count": item['count'],
                        "total_value": float(item['total_value'] or 0)
                    }
                    for item in stage_breakdown
                ]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get pipeline summary: {str(e)}"
        }


def get_leads_summary(account_id: int, status_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a summary of leads with optional filtering by status.

    Args:
        account_id: The account ID to get leads data for
        status_filter: Optional status to filter by ('new', 'contacted', 'qualified', 'unqualified')

    Returns:
        Dictionary containing lead statistics and breakdowns by status
    """
    try:
        from crm.models import Lead

        leads = Lead.objects.filter(account_id=account_id)

        if status_filter:
            leads = leads.filter(status=status_filter)

        # Overall stats
        total_leads = leads.count()

        # By status
        status_breakdown = leads.values('status').annotate(
            count=Count('id')
        ).order_by('status')

        # Recent leads (last 7 days)
        from django.utils import timezone
        from datetime import timedelta
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_leads = leads.filter(created_at__gte=seven_days_ago).count()

        return {
            "success": True,
            "leads": {
                "total_leads": total_leads,
                "recent_leads_7_days": recent_leads,
                "status_breakdown": [
                    {
                        "status": item['status'],
                        "count": item['count']
                    }
                    for item in status_breakdown
                ]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get leads summary: {str(e)}"
        }


def search_leads(query: str, account_id: int, limit: int = 10) -> Dict[str, Any]:
    """
    Search for leads by name, email, or company.

    Args:
        query: Search query string
        account_id: The account ID to search within
        limit: Maximum number of results to return (default 10)

    Returns:
        Dictionary containing list of matching leads
    """
    try:
        from crm.models import Lead

        leads = Lead.objects.filter(
            account_id=account_id
        ).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(company__icontains=query)
        )[:limit]

        return {
            "success": True,
            "results": [
                {
                    "id": lead.id,
                    "name": f"{lead.first_name} {lead.last_name}",
                    "email": lead.email,
                    "company": lead.company,
                    "status": lead.status
                }
                for lead in leads
            ],
            "count": len(leads)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to search leads: {str(e)}"
        }


def search_deals(query: str, account_id: int, limit: int = 10) -> Dict[str, Any]:
    """
    Search for deals by name or contact information.

    Args:
        query: Search query string
        account_id: The account ID to search within
        limit: Maximum number of results to return (default 10)

    Returns:
        Dictionary containing list of matching deals
    """
    try:
        from crm.models import Deal

        deals = Deal.objects.filter(
            account_id=account_id
        ).filter(
            Q(name__icontains=query) |
            Q(contact__first_name__icontains=query) |
            Q(contact__last_name__icontains=query) |
            Q(contact__company__icontains=query)
        ).select_related('contact')[:limit]

        return {
            "success": True,
            "results": [
                {
                    "id": deal.id,
                    "name": deal.name,
                    "amount": float(deal.amount) if deal.amount else 0,
                    "stage": deal.stage,
                    "probability": deal.probability,
                    "contact": f"{deal.contact.first_name} {deal.contact.last_name}"
                }
                for deal in deals
            ],
            "count": len(deals)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to search deals: {str(e)}"
        }


# Tool registry - maps function names to actual functions
AVAILABLE_TOOLS = {
    "get_lead": get_lead,
    "get_deal": get_deal,
    "get_contact": get_contact,
    "create_lead": create_lead,
    "create_deal": create_deal,
    "update_lead_status": update_lead_status,
    "update_deal_stage": update_deal_stage,
    "get_pipeline_summary": get_pipeline_summary,
    "get_leads_summary": get_leads_summary,
    "search_leads": search_leads,
    "search_deals": search_deals,
}


def get_tool_by_name(tool_name: str):
    """
    Get a tool function by its name.

    Args:
        tool_name: Name of the tool to retrieve

    Returns:
        The tool function if found, None otherwise
    """
    return AVAILABLE_TOOLS.get(tool_name)
