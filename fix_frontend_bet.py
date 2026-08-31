import re

with open('frontend/src/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the evidence_snapshot creation
old_body = '''          body: JSON.stringify({
            match_id: String(cMatch.id),
            pick: ${cMatch.homeTeam} vs : ,
            odds: parseFloat(realOdds),
            stake: parseFloat(stakeAmount),
            evidence_snapshot: JSON.stringify(insights)
          })'''

new_body = '''          body: JSON.stringify({
            match_id: String(cMatch.id),
            pick: ${cMatch.homeTeam} vs : ,
            odds: parseFloat(realOdds),
            stake: parseFloat(stakeAmount),
            evidence_snapshot: JSON.stringify({
              hermes: {
                confidence: insights.hermes?.confidence || 0,
                value_pick: insights.hermes?.value_pick || "",
                safe_pick: insights.hermes?.safe_pick || ""
              },
              home: insights.home || 0,
              draw: insights.draw || 0,
              away: insights.away || 0,
              home_xg: insights.metrics?.home_xg || 0,
              away_xg: insights.metrics?.away_xg || 0,
              over_1_5: insights.over_1_5 || 0,
              over_2_5: insights.over_2_5 || 0,
              btts_yes: insights.btts_yes || 0,
              dc_1x: insights.dc_1x || 0,
              dc_2x: insights.dc_2x || 0
            })
          })'''

content = content.replace(old_body, new_body)

with open('frontend/src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
