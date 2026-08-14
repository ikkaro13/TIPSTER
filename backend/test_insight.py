from main import get_prematch_insight
from models import PrematchInsightRequest
import traceback

try:
    req = PrematchInsightRequest(homeTeam="Rewa", awayTeam="Tupapa Maraerenga", match_id="11568282")
    res = get_prematch_insight(req)
    print("Success:", res)
except Exception as e:
    traceback.print_exc()
