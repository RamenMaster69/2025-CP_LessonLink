# lessonlinkCalendar/services.py
import requests
from icalendar import Calendar
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache

class ZamboangaEventsService:
    
    @staticmethod
    def get_nager_events():
        """Get holidays for current year AND next year"""
        try:
            current_year = datetime.now().year
            next_year = current_year + 1
            all_events = []
            
            # Get holidays for both current year and next year
            for year in [current_year, next_year]:
                url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/PH"
                
                print(f"📅 Fetching {year} holidays from Nager.Date API...")
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    holidays = response.json()
                    
                    for holiday in holidays:
                        all_events.append({
                            'id': f"nager_{holiday['date']}_{holiday['name'].replace(' ', '_')}",
                            'title': holiday['name'],
                            'description': f"{holiday.get('localName', holiday['name'])} - Public Holiday in Philippines",
                            'start_date': holiday['date'],
                            'end_date': holiday['date'],
                            'category': 'holiday',
                            'author': 'Government of Philippines',
                            'location': 'Philippines',
                            'user': {'id': None, 'is_superuser': False, 'username': 'external_event'},
                            'canEdit': False,
                            'canDelete': False,
                            'isExternal': True,
                            'source': 'nager_api'
                        })
                    
                    print(f"✅ Found {len(holidays)} holidays for {year}")
                
                else:
                    print(f"❌ Nager API returned status {response.status_code} for {year}")
            
            print(f"🎯 Total Nager events: {len(all_events)}")
            return all_events
                
        except Exception as e:
            print(f"❌ Nager API error: {e}")
            return []
    
    @staticmethod
    def get_ical_events():
        """Get events from iCal calendars for current and next year"""
        try:
            ical_urls = [
                "https://calendar.google.com/calendar/ical/en.philippines%23holiday%40group.v.calendar.google.com/public/basic.ics",
            ]
            
            all_events = []
            current_year = datetime.now().year
            next_year = current_year + 1
            
            for ical_url in ical_urls:
                try:
                    print(f"📅 Fetching iCal from: {ical_url}")
                    response = requests.get(ical_url, timeout=10)
                    
                    if response.status_code == 200:
                        cal = Calendar.from_ical(response.text)
                        events_found = 0
                        
                        for component in cal.walk():
                            if component.name == "VEVENT":
                                summary = str(component.get('summary', ''))
                                description = str(component.get('description', ''))
                                
                                # Get dates
                                start_date = component.get('dtstart').dt
                                end_date = component.get('dtend').dt
                                
                                # Handle different date formats
                                if isinstance(start_date, datetime):
                                    start_date = start_date.date()
                                if isinstance(end_date, datetime):
                                    end_date = end_date.date()
                                
                                # Include events from current year AND next year
                                if start_date.year in [current_year, next_year]:
                                    # Only include UNIQUE events not in Nager API
                                    common_holidays = [
                                        'new year', 'maundy thursday', 'good friday',
                                        'easter', 'independence', 'ninoy aquino',
                                        'national heroes', 'all saints', 'bonifacio',
                                        'immaculate conception', 'christmas', 'rizal'
                                    ]
                                    
                                    # Skip events that are already in Nager API
                                    is_common_holiday = any(holiday in summary.lower() for holiday in common_holidays)
                                    
                                    if not is_common_holiday:
                                        # Adjust for multi-day events
                                        if hasattr(end_date, '__sub__') and hasattr(start_date, '__sub__'):
                                            if (end_date - start_date).days > 1:
                                                end_date = end_date - timedelta(days=1)
                                        
                                        # Determine category
                                        category = 'holiday'
                                        if any(word in summary.lower() for word in ['festival', 'fiesta']):
                                            category = 'festival'
                                        elif any(word in summary.lower() for word in ['sports', 'race', 'regatta']):
                                            category = 'sports'
                                        
                                        all_events.append({
                                            'id': f"ical_{start_date.isoformat()}_{summary.replace(' ', '_')}",
                                            'title': summary,
                                            'description': description,
                                            'start_date': start_date.isoformat(),
                                            'end_date': end_date.isoformat() if end_date else start_date.isoformat(),
                                            'category': category,
                                            'author': 'Public Calendar',
                                            'location': 'Philippines',
                                            'user': {'id': None, 'is_superuser': False, 'username': 'external_event'},
                                            'canEdit': False,
                                            'canDelete': False,
                                            'isExternal': True,
                                            'source': 'ical_public'
                                        })
                                        events_found += 1
                        
                        print(f"✅ Found {events_found} unique iCal events")
                        
                except Exception as e:
                    print(f"❌ Error processing iCal {ical_url}: {e}")
                    continue
            
            return all_events
            
        except Exception as e:
            print(f"❌ iCal error: {e}")
            return []
    
    @staticmethod
    def get_zamboanga_events():
        """Main function - gets events without duplicates"""
        try:
            print("=== FETCHING ZAMBOANGA EVENTS (NO DUPLICATES) ===")
            
            all_events = []
            
            # Get events from Nager.Date API (primary source)
            nager_events = ZamboangaEventsService.get_nager_events()
            if nager_events:
                all_events.extend(nager_events)
            
            # Get only UNIQUE events from iCal (secondary source)
            ical_events = ZamboangaEventsService.get_ical_events()
            if ical_events:
                all_events.extend(ical_events)
            
            # Advanced duplicate removal - by date AND title
            unique_events = []
            seen_combinations = set()
            
            for event in all_events:
                # Create a unique key using date + first 3 words of title
                event_key = f"{event['start_date']}_{event['title'].lower().replace(' ', '_')}"
                
                if event_key not in seen_combinations:
                    seen_combinations.add(event_key)
                    unique_events.append(event)
                else:
                    print(f"🔄 Removing duplicate: {event['start_date']} - {event['title']}")
            
            # Sort events by date
            unique_events.sort(key=lambda x: x['start_date'])
            
            print(f"🎯 Final unique events: {len(unique_events)}")
            
            # Show what events we found
            for event in unique_events:
                print(f"   📌 {event['start_date']}: {event['title']} ({event['source']})")
            
            if unique_events:
                return unique_events
            else:
                print("⚠️ No events found from APIs")
                return []
            
        except Exception as e:
            print(f"❌ Error in Zamboanga events service: {e}")
            return []