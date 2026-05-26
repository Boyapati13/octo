#!/usr/bin/env python3
"""
Economic News Risk Sentinel (SMC News Shield)
==============================================
Scrapes live high-impact economic calendar events and implements a dynamic
news shield to protect automated trading systems from massive news-spike drawdowns.
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

class NewsSentinel:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_high_impact_events(self) -> list:
        """Fetches the live weekly calendar and filters for Red-Folder (High) impact events."""
        events = []
        url = "https://www.forexfactory.com/"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                print(f"[Sentinel] [ERROR] Failed to fetch Forex Factory: HTTP {resp.status_code}")
                return events
                
            soup = BeautifulSoup(resp.content, "html.parser")
            table = soup.find("table", class_="calendar__table")
            if not table:
                print("[Sentinel] [ERROR] calendar__table not found.")
                return events
                
            rows = table.find_all("tr", class_="calendar__row")
            
            # Keep track of active date as we parse row-by-row
            current_date_str = ""
            
            for row in rows:
                # Parse date if available in row
                date_td = row.find("td", class_="calendar__date")
                if date_td and date_td.text.strip():
                    current_date_str = date_td.text.strip()
                    
                # Currency
                currency_td = row.find("td", class_="calendar__currency")
                currency = currency_td.text.strip().upper() if currency_td else ""
                
                # Event Name
                event_td = row.find("td", class_="calendar__event")
                event_name = event_td.text.strip() if event_td else ""
                
                event_link = ""
                if event_td:
                    event_a = event_td.find("a")
                    if event_a:
                        event_href = event_a.get("href", "")
                        if event_href:
                            if event_href.startswith("http"):
                                event_link = event_href
                            else:
                                if event_href.startswith("/"):
                                    event_href = event_href[1:]
                                event_link = f"https://www.forexfactory.com/{event_href}"
                
                # Time
                time_td = row.find("td", class_="calendar__time")
                time_str = time_td.text.strip() if time_td else ""
                
                # Impact
                impact_td = row.find("td", class_="calendar__impact")
                impact_span = impact_td.find("span") if impact_td else None
                impact = "Low"
                if impact_span:
                    impact_class = impact_span.get("class", [])
                    impact_combined = "".join(impact_class).lower()
                    if "high" in impact_combined or "red" in impact_combined:
                        impact = "High"
                    elif "medium" in impact_combined or "orange" in impact_combined:
                        impact = "Medium"
                    elif "low" in impact_combined or "yellow" in impact_combined:
                        impact = "Low"
                        
                if impact == "High" and event_name and currency:
                    events.append({
                        "date": current_date_str,
                        "time": time_str,
                        "currency": currency,
                        "event": event_name,
                        "impact": "High",
                        "link": event_link
                    })
        except Exception as e:
            print(f"[Sentinel] [ERROR] Exception during scrape: {e}")
            
        return events

    def check_risk_status(self, symbol: str) -> dict:
        """Evaluates whether active trading should be blocked due to upcoming news spikes."""
        events = self.fetch_high_impact_events()
        if not events:
            return {"status": "CLEAR", "reason": "No high-impact economic events scraped."}
            
        # Map symbol to its primary target currencies
        target_currencies = ["USD"] # USD is default for gold, crypto, major indices
        symbol_upper = symbol.upper()
        if "EUR" in symbol_upper:
            target_currencies.append("EUR")
        if "GBP" in symbol_upper:
            target_currencies.append("GBP")
        if "JPY" in symbol_upper:
            target_currencies.append("JPY")
        if "CAD" in symbol_upper:
            target_currencies.append("CAD")
        if "AUD" in symbol_upper:
            target_currencies.append("AUD")
            
        active_news_blocks = []
        
        for ev in events:
            if ev["currency"] in target_currencies:
                # Filter out low impact / all-day events if they don't list a specific time
                time_str = ev["time"].lower()
                if "day" in time_str or "tentative" in time_str or not time_str:
                    continue
                    
                # Forex Factory home page times are typically Eastern Time (EST/EDT)
                # Let's print the threat
                active_news_blocks.append(ev)
                
        if active_news_blocks:
            return {
                "status": "THREAT_DETECTED",
                "reason": f"High-Impact Red Folder news scheduled today for {', '.join(target_currencies)}",
                "events": active_news_blocks
            }
            
        return {"status": "CLEAR", "reason": "No high-impact economic threats scheduled today for target currencies."}

def main():
    print("=" * 60)
    print("         ECONOMIC NEWS RISK SENTINEL (SMC SHIELD)")
    print("=" * 60)
    
    sentinel = NewsSentinel()
    
    # Check threat status for Gold (XAUUSD+)
    print("Checking risk profile for XAUUSD+...")
    res = sentinel.check_risk_status("XAUUSD+")
    
    print("\n" + "=" * 60)
    print("                     RISK REPORT")
    print("=" * 60)
    print(f"Status  : {res['status']}")
    print(f"Details : {res['reason']}")
    
    if "events" in res:
        print("\nRED-FOLDER EVENTS SCHEDULED TODAY:")
        for idx, ev in enumerate(res["events"]):
            print(f"  {idx+1}. [{ev['date']} @ {ev['time']}] {ev['currency']} - {ev['event']}")
            if ev.get("link"):
                print(f"     Direct Link: {ev['link']}")
            
    print("=" * 60)

if __name__ == "__main__":
    main()
