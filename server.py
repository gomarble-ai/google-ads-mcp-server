from fastmcp import FastMCP, Context
from typing import Any, Dict, List, Optional
import os
import logging
import requests

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

# Import OAuth modules after environment is loaded
from oauth.google_auth import format_customer_id, get_headers_with_auto_token, execute_gaql

# Get environment variables
GOOGLE_ADS_DEVELOPER_TOKEN = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('google_ads_server')

mcp = FastMCP("Google Ads Tools")

# Server startup
logger.info("Starting Google Ads MCP Server...")

def get_customer_name(customer_id: str) -> str:
    """Retrieve descriptive_name for the given customer ID."""
    try:
        query = "SELECT customer.descriptive_name FROM customer"
        result = execute_gaql(customer_id, query)
        rows = result.get('results', [])
        if not rows:
            return "Name not available (no results)"
        customer = rows[0].get('customer', {})
        return customer.get('descriptiveName', "Name not available (missing field)")
    except Exception:
        return "Name not available (error)"

def is_manager_account(customer_id: str) -> bool:
    """Check if a customer account is a manager (MCC)."""
    try:
        query = "SELECT customer.manager FROM customer"
        result = execute_gaql(customer_id, query)
        rows = result.get('results', [])
        if not rows:
            return False
        return bool(rows[0].get('customer', {}).get('manager', False))
    except Exception:
        return False

def get_sub_accounts(manager_id: str) -> List[Dict[str, Any]]:
    """List sub-accounts under a manager account."""
    try:
        query = (
            "SELECT customer_client.id, customer_client.descriptive_name, "
            "customer_client.level, customer_client.manager "
            "FROM customer_client WHERE customer_client.level > 0"
        )
        result = execute_gaql(manager_id, query)
        rows = result.get('results', [])
        subs = []
        for row in rows:
            client = row.get('customerClient', {}) or row.get('customer_client', {})
            cid = format_customer_id(str(client.get('id', '')))
            subs.append({
                'id': cid,
                'name': client.get('descriptiveName', f"Sub-account {cid}"),
                'access_type': 'managed',
                'is_manager': bool(client.get('manager', False)),
                'parent_id': manager_id,
                'level': int(client.get('level', 0))
            })
        return subs
    except Exception:
        return []

@mcp.tool
def run_gaql(
    customer_id: str,
    query: str,
    manager_id: str = "",
    ctx: Context = None
) -> Dict[str, Any]:
    """Execute GAQL using the non-streaming search endpoint for consistent JSON parsing."""
    if ctx:
        ctx.info(f"Executing GAQL query for customer {customer_id}...")
        ctx.info(f"Query: {query}")

    if not GOOGLE_ADS_DEVELOPER_TOKEN:
        raise ValueError("Google Ads Developer Token is not set in environment variables.")

    try:
        # This will automatically trigger OAuth flow if needed
        result = execute_gaql(customer_id, query, manager_id)
        if ctx:
            ctx.info(f"GAQL query successful. Found {result['totalRows']} rows.")
        return result
    except Exception as e:
        if ctx:
            ctx.error(f"GAQL query failed: {str(e)}")
        raise

@mcp.tool
def list_accounts(ctx: Context = None) -> Dict[str, Any]:
    """List all accessible accounts including nested sub-accounts."""
    if ctx:
        ctx.info("Checking credentials and preparing to list accounts...")

    if not GOOGLE_ADS_DEVELOPER_TOKEN:
        raise ValueError("Google Ads Developer Token is not set in environment variables.")

    try:
        # This will automatically trigger OAuth flow if needed
        headers = get_headers_with_auto_token()
        
        # Fetch top-level accessible customers
        url = "https://googleads.googleapis.com/v19/customers:listAccessibleCustomers"
        resp = requests.get(url, headers=headers)
        if not resp.ok:
            if ctx:
                ctx.error(f"Failed to list accessible accounts: {resp.status_code} {resp.reason}")
            raise Exception(
                f"Error listing accounts: {resp.status_code} {resp.reason} - {resp.text}"
            )
        data = resp.json()
        resource_names = data.get('resourceNames', [])
        if not resource_names:
            if ctx:
                ctx.info("No accessible Google Ads accounts found.")
            return {'accounts': [], 'message': 'No accessible accounts found.'}

        if ctx:
            ctx.info(f"Found {len(resource_names)} top-level accessible accounts. Fetching details...")

        accounts = []
        seen = set()
        for resource in resource_names:
            cid = resource.split('/')[-1]
            fid = format_customer_id(cid)
            name = get_customer_name(fid)
            manager = is_manager_account(fid)
            account = {
                'id': fid,
                'name': name,
                'access_type': 'direct',
                'is_manager': manager,
                'level': 0
            }
            accounts.append(account)
            seen.add(fid)
            # Include sub-accounts (and nested)
            if manager:
                subs = get_sub_accounts(fid)
                for sub in subs:
                    if sub['id'] not in seen:
                        accounts.append(sub)
                        seen.add(sub['id'])
                        # nested level
                        if sub['is_manager']:
                            nested = get_sub_accounts(sub['id'])
                            for n in nested:
                                if n['id'] not in seen:
                                    accounts.append(n)
                                    seen.add(n['id'])

        if ctx:
            ctx.info(f"Finished processing. Found a total of {len(accounts)} accounts.")

        return {
            'accounts': accounts,
            'total_accounts': len(accounts)
        }
    except Exception as e:
        if ctx:
            ctx.error(f"Error listing accounts: {str(e)}")
        raise

@mcp.tool
def run_keyword_planner(
    customer_id: str,
    keywords: List[str],
    manager_id: str = "",
    page_url: Optional[str] = None,
    start_year: Optional[int] = None,
    start_month: Optional[str] = None,
    end_year: Optional[int] = None,
    end_month: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """Generate keyword ideas using Google Ads KeywordPlanIdeaService.

    This tool allows you to generate keyword ideas based on seed keywords or a page URL. 
    You can specify targeting parameters such as language, location, and network to refine your keyword suggestions.

    Args:
        customer_id: The Google Ads customer ID (10 digits, no dashes)
        keywords: A list of seed keywords to generate ideas from
        manager_id: Manager ID if access type is 'managed'
        page_url: Optional page URL related to your business to generate ideas from
        start_year: Optional start year for historical data (defaults to previous year)
        start_month: Optional start month for historical data (defaults to JANUARY)
        end_year: Optional end year for historical data (defaults to current year)
        end_month: Optional end month for historical data (defaults to current month)

    Returns:
        A list of keyword ideas with associated metrics

    Note:
        - At least one of 'keywords' or 'page_url' must be provided
        - Ensure that the 'customer_id' is formatted as a string, even if it appears numeric
        - Valid months: JANUARY, FEBRUARY, MARCH, APRIL, MAY, JUNE, JULY, AUGUST, SEPTEMBER, OCTOBER, NOVEMBER, DECEMBER
    """
    if ctx:
        ctx.info(f"Generating keyword ideas for customer {customer_id}...")
        if keywords:
            ctx.info(f"Seed keywords: {', '.join(keywords)}")
        if page_url:
            ctx.info(f"Page URL: {page_url}")

    if not GOOGLE_ADS_DEVELOPER_TOKEN:
        raise ValueError("Google Ads Developer Token is not set in environment variables.")
    
    # Validate that at least one of keywords or page_url is provided
    if (not keywords or len(keywords) == 0) and not page_url:
        raise ValueError("At least one of keywords or page URL is required, but neither was specified.")
    
    try:
        # This will automatically trigger OAuth flow if needed
        headers = get_headers_with_auto_token()
        
        formatted_customer_id = format_customer_id(customer_id)
        url = f"https://googleads.googleapis.com/v19/customers/{formatted_customer_id}:generateKeywordIdeas"
        
        if manager_id:
            headers['login-customer-id'] = format_customer_id(manager_id)
        
        # Set up dynamic date range with user-provided values or smart defaults
        from datetime import datetime
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.strftime('%B').upper()
        
        valid_months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
                        'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']
        
        # Use provided dates or fall back to defaults
        start_year_final = start_year or (current_year - 1)
        start_month_final = start_month.upper() if start_month and start_month.upper() in valid_months else 'JANUARY'
        end_year_final = end_year or current_year
        end_month_final = end_month.upper() if end_month and end_month.upper() in valid_months else current_month
        
        # Build the request body according to Google Ads API specification
        request_body = {
            'language': 'languageConstants/1000',
            'geoTargetConstants': ['geoTargetConstants/2840'],
            'keywordPlanNetwork': 'GOOGLE_SEARCH_AND_PARTNERS',
            'includeAdultKeywords': False,
            'pageSize': 25,
            'historicalMetricsOptions': {
                'yearMonthRange': {
                    'start': {
                        'year': start_year_final,
                        'month': start_month_final
                    },
                    'end': {
                        'year': end_year_final,
                        'month': end_month_final
                    }
                }
            }
        }
        
        # Set the appropriate seed based on what's provided
        if (not keywords or len(keywords) == 0) and page_url:
            request_body['urlSeed'] = {'url': page_url}
        elif keywords and len(keywords) > 0 and not page_url:
            request_body['keywordSeed'] = {'keywords': keywords}
        elif keywords and len(keywords) > 0 and page_url:
            request_body['keywordAndUrlSeed'] = {
                'url': page_url,
                'keywords': keywords
            }
        
        response = requests.post(url, headers=headers, json=request_body)
        
        if not response.ok:
            error_text = response.text
            if ctx:
                ctx.error(f"Keyword planner request failed: {response.status_code} {response.reason}")
            raise Exception(f"Error executing request: {response.status_code} {response.reason} - {error_text}")
        
        results = response.json()
        
        if 'results' not in results or not results['results']:
            message = f"No keyword ideas found for the provided inputs.\n\nKeywords: {', '.join(keywords) if keywords else 'None'}\nPage URL: {page_url or 'None'}\nAccount: {formatted_customer_id}"
            if ctx:
                ctx.info(message)
            return {
                "message": message,
                "keywords": keywords or [],
                "page_url": page_url,
                "date_range": f"{start_month_final} {start_year_final} to {end_month_final} {end_year_final}"
            }
        
        # Format the results for better readability
        formatted_results = []
        for result in results['results']:
            keyword_idea = result.get('keywordIdeaMetrics', {})
            keyword_text = result.get('text', 'N/A')
            
            formatted_result = {
                'keyword': keyword_text,
                'avg_monthly_searches': keyword_idea.get('avgMonthlySearches', 'N/A'),
                'competition': keyword_idea.get('competition', 'N/A'),
                'competition_index': keyword_idea.get('competitionIndex', 'N/A'),
                'low_top_of_page_bid_micros': keyword_idea.get('lowTopOfPageBidMicros', 'N/A'),
                'high_top_of_page_bid_micros': keyword_idea.get('highTopOfPageBidMicros', 'N/A')
            }
            formatted_results.append(formatted_result)
        
        if ctx:
            ctx.info(f"Found {len(formatted_results)} keyword ideas.")
        
        return {
            "keyword_ideas": formatted_results,
            "total_ideas": len(formatted_results),
            "input_keywords": keywords or [],
            "input_page_url": page_url,
            "date_range": f"{start_month_final} {start_year_final} to {end_month_final} {end_year_final}"
        }
        
    except Exception as e:
        if ctx:
            ctx.error(f"An unexpected error occurred: {e}")
        raise

@mcp.resource("gaql://reference")
def gaql_reference() -> str:
    """Google Ads Query Language (GAQL) reference documentation."""
    return """Schema Format:    
                ## Basic Query Structure
                '''
                SELECT field1, field2, ... 
                FROM resource_type
                WHERE condition
                ORDER BY field [ASC|DESC]
                LIMIT n
                '''

                ## Common Field Types

                ### Resource Fields
                - campaign.id, campaign.name, campaign.status
                - ad_group.id, ad_group.name, ad_group.status
                - ad_group_ad.ad.id, ad_group_ad.ad.final_urls
                - ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type (for keyword_view)

                ### Metric Fields
                - metrics.impressions
                - metrics.clicks
                - metrics.cost_micros
                - metrics.conversions
                - metrics.conversions_value (direct conversion revenue - primary revenue metric)
                - metrics.ctr
                - metrics.average_cpc

                ### Segment Fields
                - segments.date
                - segments.device
                - segments.day_of_week

                ## Common WHERE Clauses

                ### Date Ranges
                - WHERE segments.date DURING LAST_7_DAYS
                - WHERE segments.date DURING LAST_30_DAYS
                - WHERE segments.date BETWEEN '2023-01-01' AND '2023-01-31'

                ### Filtering
                - WHERE campaign.status = 'ENABLED'
                - WHERE metrics.clicks > 100
                - WHERE campaign.name LIKE '%Brand%'
                - Use LIKE '%keyword%' instead of CONTAINS 'keyword' (CONTAINS not supported)

                EXAMPLE QUERIES:

                1. Basic campaign metrics:
                SELECT 
                campaign.id,
                campaign.name, 
                metrics.clicks, 
                metrics.impressions,
                metrics.cost_micros
                FROM campaign 
                WHERE segments.date DURING LAST_7_DAYS

                2. Ad group performance:
                SELECT 
                campaign.id,
                ad_group.name, 
                metrics.conversions, 
                metrics.cost_micros,
                campaign.name
                FROM ad_group 
                WHERE metrics.clicks > 100

                3. Keyword analysis (CORRECT field names):
                SELECT 
                campaign.id,
                ad_group_criterion.keyword.text, 
                ad_group_criterion.keyword.match_type,
                metrics.average_position, 
                metrics.ctr
                FROM keyword_view 
                WHERE segments.date DURING LAST_30_DAYS
                ORDER BY metrics.impressions DESC

                4. Get conversion data with revenue:
                SELECT
                campaign.id,
                campaign.name,
                metrics.conversions,
                metrics.conversions_value,
                metrics.all_conversions_value,
                metrics.cost_micros
                FROM campaign
                WHERE segments.date DURING LAST_30_DAYS

                IMPORTANT NOTES & COMMON ERRORS TO AVOID:

                ### Field Errors to Avoid:
                WRONG: campaign.campaign_budget.amount_micros
                CORRECT: campaign_budget.amount_micros (query from campaign_budget resource)

                WRONG: keyword.text, keyword.match_type  
                CORRECT: ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type

                ### Required Fields:
                - Always include campaign.id when querying ad_group, keyword_view, or other campaign-related resources
                - Some resources require specific reference fields in SELECT clause

                ### Revenue Metrics:
                - metrics.conversions_value = Direct conversion revenue (use for ROI calculations)
                - metrics.all_conversions_value = Total attributed revenue (includes view-through)

                ### String Matching:
                - Use LIKE '%keyword%' not CONTAINS 'keyword'
                - GAQL does not support CONTAINS operator

                NOTE:
                - Date ranges must be finite: LAST_7_DAYS, LAST_30_DAYS, or BETWEEN dates
                - Cannot use open-ended ranges like >= '2023-01-31'
                - Always include campaign.id when error messages request it."""

if __name__ == "__main__":
    import sys
    
    # Check command line arguments for transport mode
    if "--http" in sys.argv:
        logger.info("Starting with HTTP transport on http://127.0.0.1:8000/mcp")
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")
    else:
        # Default to STDIO for Claude Desktop compatibility
        logger.info("Starting with STDIO transport for Claude Desktop")
        mcp.run(transport="stdio")