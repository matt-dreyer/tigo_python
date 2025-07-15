# examples/basic_usage.py
import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Fix import path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tigo_python.client import TigoClient

# Fix Unicode encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Load environment variables
load_dotenv()
USERNAME = os.getenv("TIGO_USERNAME")
PASSWORD = os.getenv("TIGO_PASSWORD")

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")

def display_dataframe(df: pd.DataFrame, title: str, max_rows: int = 10):
    """Display a DataFrame with formatting."""
    print_subsection(title)
    if df.empty:
        print("No data available")
    else:
        print(f"Shape: {df.shape}")
        print(df.head(max_rows).to_string())
        if len(df) > max_rows:
            print(f"... ({len(df) - max_rows} more rows)")

def get_status_icon(status: str) -> str:
    """Get status icon that works on all systems."""
    icons = {
        "success": "[OK]",
        "warning": "[WARN]", 
        "error": "[ERROR]",
        "info": "[INFO]"
    }
    return icons.get(status, "[?]")

def main():
    """Main execution function using context manager."""
    
    print("Tigo Energy API - Enhanced Usage Example")
    print("=" * 60)
    
    # Use context manager for automatic cleanup
    with TigoClient(USERNAME, PASSWORD) as client:
        print(f"{get_status_icon('success')} Successfully logged in!")
        
        # ===========================================
        # BASIC SYSTEM INFORMATION
        # ===========================================
        print_section("BASIC SYSTEM INFORMATION")
        
        print_subsection("User Information")
        user = client.get_user()
        print(f"User: {user['user']['first_name']} {user['user']['last_name']}")
        print(f"Email: {user['user']['email']}")
        print(f"Systems: {user['user']['systemCount']}")
        
        print_subsection("Available Systems")
        systems = client.list_systems()
        for i, system in enumerate(systems["systems"]):
            print(f"{i+1}. {system['name']} (ID: {system['system_id']})")
            print(f"   Location: {system['city']}, {system['state']}")
            print(f"   Power Rating: {system['power_rating']/1000:.1f} kW")
            print(f"   Status: {system['status']}")
        
        if not systems["systems"]:
            print(f"{get_status_icon('error')} No systems found!")
            return
        
        # Use first system for detailed analysis
        system = systems["systems"][0]
        system_id = system["system_id"]
        print(f"\n{get_status_icon('info')} Using system: {system['name']} (ID: {system_id})")
        
        # ===========================================
        # SYSTEM DETAILS
        # ===========================================
        print_section("SYSTEM DETAILS")
        
        print_subsection("System Configuration")
        layout = client.get_system_layout(system_id)
        inverters = layout["system"]["inverters"]
        
        total_panels = 0
        for inverter in inverters:
            print(f"Inverter: {inverter['label']}")
            for mppt in inverter.get('mppts', []):
                print(f"  MPPT: {mppt['label']}")
                for string in mppt.get('strings', []):
                    panel_count = len(string.get('panels', []))
                    total_panels += panel_count
                    print(f"    {string['label']}: {panel_count} panels")
        
        print(f"\nTotal Panels: {total_panels}")
        
        print_subsection("Data Sources")
        sources = client.get_sources(system_id)
        for source in sources["sources"]:
            print(f"Source: {source['name']} ({source['serial']})")
            print(f"  Last Check-in: {source['last_checkin']}")
            print(f"  Control State: {source['control_state']}")
            print(f"  Panels: {source['panel_count']}")
        
        # ===========================================
        # CURRENT PERFORMANCE
        # ===========================================
        print_section("CURRENT PERFORMANCE")
        
        print_subsection("System Summary")
        summary = client.get_summary(system_id)['summary']
        
        # Convert to more readable units
        lifetime_kwh = summary['lifetime_energy_dc'] / 1000
        daily_kwh = summary['daily_energy_dc'] / 1000
        ytd_kwh = summary['ytd_energy_dc'] / 1000
        current_kw = summary['last_power_dc'] / 1000
        
        print(f"Current Power: {current_kw:.2f} kW")
        print(f"Today's Energy: {daily_kwh:.2f} kWh")
        print(f"Year-to-Date: {ytd_kwh:.1f} kWh")
        print(f"Lifetime Energy: {lifetime_kwh:.1f} kWh")
        print(f"Last Update: {summary['updated_on']}")
        
        # ===========================================
        # DATA ANALYSIS
        # ===========================================
        print_section("DATA ANALYSIS")
        
        try:
            # Today's performance - use hourly data instead of minute-by-minute
            print_subsection("Today's Performance")
            today_df = client.get_today_data(system_id)
            if not today_df.empty:
                # Filter out NaN values for cleaner stats
                valid_data = today_df.iloc[:, 0].dropna()
                if len(valid_data) > 0:
                    print(f"Data points today: {len(valid_data)} (hourly readings)")
                    print(f"Peak power: {valid_data.max():.0f} W")
                    print(f"Average power: {valid_data.mean():.0f} W")
                    print(f"Current power: {valid_data.iloc[-1] if len(valid_data) > 0 else 0:.0f} W")
                else:
                    print("No valid power data available for today")
            else:
                print("No data available for today")
            
            # Weekly trend analysis - daily totals only
            print_subsection("Weekly Performance Trend")
            week_df = client.get_date_range_data(system_id, days_back=7, level="day")
            if not week_df.empty:
                print("Daily energy production (last 7 days):")
                daily_energy = week_df.iloc[:, 0].dropna() / 1000  # Convert to kWh
                
                # Only show actual unique dates, not duplicates
                daily_totals = {}
                for date, energy in daily_energy.items():
                    date_str = date.strftime('%Y-%m-%d')
                    if date_str not in daily_totals:
                        daily_totals[date_str] = energy
                    else:
                        daily_totals[date_str] += energy  # Sum if multiple entries per day
                
                # Sort by date and display
                for date_str in sorted(daily_totals.keys()):
                    energy = daily_totals[date_str]
                    print(f"  {date_str}: {energy:.1f} kWh")
                
                total_week = sum(daily_totals.values())
                avg_daily = total_week / len(daily_totals) if daily_totals else 0
                
                print(f"\nWeek total: {total_week:.1f} kWh")
                print(f"Daily average: {avg_daily:.1f} kWh")
            else:
                print("No weekly data available")
                
        except Exception as e:
            print(f"{get_status_icon('warning')} Data analysis error: {e}")
        
        # ===========================================
        # SYSTEM EFFICIENCY ANALYSIS
        # ===========================================
        print_section("SYSTEM EFFICIENCY ANALYSIS")
        
        try:
            print_subsection("Efficiency Metrics (Daylight Hours Only)")
            efficiency = client.calculate_system_efficiency(system_id, days_back=14)
            
            if "error" in efficiency:
                print(f"{get_status_icon('error')} {efficiency['error']}")
            else:
                print(f"Rated Power: {efficiency['rated_power_dc']/1000:.1f} kW")
                print(f"Peak Power: {efficiency['peak_power']:.0f} W ({efficiency['peak_efficiency']:.1f}% of rated)")
                print(f"Average Power (daylight): {efficiency['average_power_daylight']:.0f} W")
                print(f"Daylight Efficiency: {efficiency['average_efficiency_percent']:.1f}%")
                print(f"Capacity Factor: {efficiency['capacity_factor']:.1f}%")
                print(f"Analysis Period: {efficiency['analysis_period_days']} days")
                print(f"Data Resolution: {efficiency.get('data_resolution', 'unknown')}")
                print(f"Productive Hours/Day: {efficiency['avg_productive_hours_per_day']:.1f} hours")
                print(f"Daylight Hours/Day: {efficiency.get('avg_daylight_hours_per_day', 0):.1f} hours")
                
                # Performance rating with adjusted thresholds
                eff_pct = efficiency['average_efficiency_percent']
                if eff_pct > 75:
                    rating = "[EXCELLENT]"
                elif eff_pct > 60:
                    rating = "[GOOD]"
                elif eff_pct > 45:
                    rating = "[FAIR]"
                elif eff_pct > 30:
                    rating = "[ACCEPTABLE]"
                else:
                    rating = "[POOR]"
                
                print(f"Performance Rating: {rating}")
                
                # Add helpful context
                print(f"\nNote: Analysis excludes nighttime hours (typically 6 AM - 8 PM productive)")
                print(f"Your system is achieving {eff_pct:.1f}% of its rated capacity during daylight hours.")
                
        except Exception as e:
            print(f"{get_status_icon('warning')} Efficiency analysis error: {e}")
        
        # ===========================================
        # PANEL-LEVEL ANALYSIS
        # ===========================================
        print_section("PANEL-LEVEL ANALYSIS")
        
        try:
            print_subsection("Individual Panel Performance")
            panel_perf = client.get_panel_performance(system_id, days_back=7)
            
            if not panel_perf.empty:
                print("Top 5 performing panels:")
                display_dataframe(panel_perf.head(), "Top Performers", max_rows=5)
                
                print_subsection("Underperforming Panel Detection")
                problems = client.find_underperforming_panels(
                    system_id, 
                    threshold_percent=85.0, 
                    days_back=7
                )
                
                if problems:
                    print(f"{get_status_icon('warning')} Found {len(problems)} panels performing below 85%:")
                    for panel in problems:
                        print(f"  Panel {panel['panel_id']}: {panel['efficiency_percent']:.1f}% efficiency")
                        print(f"    Average: {panel['mean_power']:.0f}W, Peak: {panel['max_power']:.0f}W")
                else:
                    print(f"{get_status_icon('success')} All panels performing above 85% threshold")
            else:
                print("No panel-level data available")
                
        except Exception as e:
            print(f"{get_status_icon('warning')} Panel analysis error: {e}")
        
        # ===========================================
        # ALERTS AND MONITORING
        # ===========================================
        print_section("ALERTS AND MONITORING")
        
        print_subsection("Active Alerts")
        alerts = client.get_alerts(system_id)
        
        if alerts["alerts"]:
            for alert in alerts["alerts"]:
                print(f"{get_status_icon('warning')} {alert['title']}")
                print(f"   Generated: {alert['generated']}")
                print(f"   Message: {alert['message'][:100]}...")
        else:
            print(f"{get_status_icon('success')} No active alerts")
        
        print_subsection("Available Alert Types")
        alert_types = client.get_alert_types()
        print(f"System monitors for {len(alert_types['alert_types'])} types of issues:")
        for alert_type in alert_types['alert_types'][:5]:  # Show first 5
            print(f"  - {alert_type['title']}")
        if len(alert_types['alert_types']) > 5:
            print(f"  ... and {len(alert_types['alert_types']) - 5} more")
        
        # ===========================================
        # RAW DATA SAMPLES
        # ===========================================
        print_section("RAW DATA SAMPLES")
        
        try:
            # Show CSV data format - get last 24 hours of minute-level data
            start_date = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
            end_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
            print_subsection("Recent Combined Data - Last 24 Hours (15-Minute Aggregation)")
            # Get raw CSV data instead of DataFrame
            combined_csv = client.get_combined_data_raw(system_id, start=start_date, end=end_date, level="minute")
            
            if combined_csv and combined_csv.strip():
                lines = combined_csv.strip().split('\n')
                print(f"Raw headers: {lines[0] if lines else 'No data'}")
                
                if len(lines) > 1:
                    data_rows = lines[1:]  # Skip header
                    print(f"Raw data points: {len(data_rows)} (minute-by-minute)")
                    print(f"Time period: Last 24 hours")
                    
                    # Parse and aggregate data into 15-minute chunks
                    try:
                        aggregated_data = []
                        current_chunk = []
                        current_timestamp = None
                        chunk_start_time = None
                        
                        for line in data_rows:
                            parts = line.split(',')
                            if len(parts) >= 2:
                                timestamp_str = parts[0]
                                power_str = parts[1]
                                
                                # Parse timestamp
                                try:
                                    timestamp = datetime.strptime(timestamp_str, '%Y/%m/%d %H:%M:%S')
                                except ValueError:
                                    try:
                                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                    except ValueError:
                                        continue
                                
                                # Parse power value
                                try:
                                    power = float(power_str) if power_str.replace('.','').replace('-','').isdigit() else 0
                                except ValueError:
                                    power = 0
                                
                                # Determine 15-minute chunk (round down to nearest 15 minutes)
                                chunk_minute = (timestamp.minute // 15) * 15
                                chunk_time = timestamp.replace(minute=chunk_minute, second=0, microsecond=0)
                                
                                # If this is a new chunk, process the previous one
                                if current_timestamp is None:
                                    current_timestamp = chunk_time
                                    chunk_start_time = timestamp
                                elif chunk_time != current_timestamp:
                                    # Process current chunk
                                    if current_chunk:
                                        avg_power = sum(current_chunk) / len(current_chunk)
                                        max_power = max(current_chunk)
                                        min_power = min(current_chunk)
                                        aggregated_data.append({
                                            'timestamp': current_timestamp,
                                            'avg_power': avg_power,
                                            'max_power': max_power,
                                            'min_power': min_power,
                                            'readings': len(current_chunk)
                                        })
                                    
                                    # Start new chunk
                                    current_timestamp = chunk_time
                                    current_chunk = []
                                    chunk_start_time = timestamp
                                
                                current_chunk.append(power)
                        
                        # Process the last chunk
                        if current_chunk:
                            avg_power = sum(current_chunk) / len(current_chunk)
                            max_power = max(current_chunk)
                            min_power = min(current_chunk)
                            aggregated_data.append({
                                'timestamp': current_timestamp,
                                'avg_power': avg_power,
                                'max_power': max_power,
                                'min_power': min_power,
                                'readings': len(current_chunk)
                            })
                        
                        # Display aggregated data
                        print(f"\nAggregated into {len(aggregated_data)} 15-minute chunks:")
                        print("     #  Time                Avg Power  Max Power  Min Power  Readings")
                        print("   " + "-" * 70)
                        
                        for i, chunk in enumerate(aggregated_data, 1):
                            timestamp = chunk['timestamp'].strftime('%Y-%m-%d %H:%M')
                            avg_power = chunk['avg_power']
                            max_power = chunk['max_power']
                            min_power = chunk['min_power']
                            readings = chunk['readings']
                            
                            print(f"  {i:3d}. {timestamp}   {avg_power:8.0f}W  {max_power:8.0f}W  {min_power:8.0f}W    {readings:2d}")
                        
                        # Calculate 24-hour summary from aggregated data
                        print(f"\n--- 24-Hour Summary (from 15-min chunks) ---")
                        if aggregated_data:
                            all_avg_powers = [chunk['avg_power'] for chunk in aggregated_data]
                            all_max_powers = [chunk['max_power'] for chunk in aggregated_data]
                            
                            total_chunks = len(aggregated_data)
                            peak_power = max(all_max_powers)
                            min_power = min([chunk['min_power'] for chunk in aggregated_data])
                            avg_power_24h = sum(all_avg_powers) / len(all_avg_powers)
                            
                            # Find peak time
                            peak_chunk = max(aggregated_data, key=lambda x: x['max_power'])
                            peak_time = peak_chunk['timestamp'].strftime('%Y-%m-%d %H:%M')
                            
                            # Estimate energy (sum of 15-min averages × 0.25 hours)
                            energy_kwh = sum(all_avg_powers) * 0.25 / 1000  # 15 min = 0.25 hours
                            
                            # Count productive chunks (>50W average)
                            productive_chunks = len([c for c in aggregated_data if c['avg_power'] > 50])
                            
                            print(f"Total 15-min chunks: {total_chunks}")
                            print(f"Peak power: {peak_power:,.0f} W at {peak_time}")
                            print(f"Min power: {min_power:,.0f} W")
                            print(f"Avg power (24h): {avg_power_24h:,.0f} W")
                            print(f"Estimated energy (24h): {energy_kwh:.2f} kWh")
                            print(f"Productive chunks (>50W): {productive_chunks} ({productive_chunks * 0.25:.1f} hours)")
                            print(f"Low/nighttime chunks: {total_chunks - productive_chunks}")
                            
                            # Show trend from first to last chunk
                            if len(aggregated_data) >= 2:
                                start_power = aggregated_data[0]['avg_power']
                                end_power = aggregated_data[-1]['avg_power']
                                change = end_power - start_power
                                start_time = aggregated_data[0]['timestamp'].strftime('%H:%M')
                                end_time = aggregated_data[-1]['timestamp'].strftime('%H:%M')
                                print(f"Power trend: {change:+.0f}W ({start_time}: {start_power:.0f}W → {end_time}: {end_power:.0f}W)")
                        
                    except Exception as e:
                        print(f"Error processing aggregation: {e}")
                        # Fallback to original display
                        print("\nFalling back to raw data sample:")
                        for i, line in enumerate(data_rows[:10], 1):
                            parts = line.split(',')
                            if len(parts) >= 2:
                                timestamp = parts[0]
                                power = parts[1]
                                print(f"  {i:3d}. {timestamp} | {power:>6} W")
                else:
                    print("No data rows found")
            else:
                print("No CSV data available for the last 24 hours")
            
            # Also show aggregate data sample for comparison
            print_subsection("Aggregate Data Sample (Panel-Level)")
            try:
                # Get a few panel IDs for sample
                objects = client.get_objects(system_id)
                panel_objects = [obj for obj in objects.get("objects", []) 
                               if obj.get("object_type_id") == 2][:3]  # First 3 panels
                
                if panel_objects:
                    panel_ids = [str(obj["id"]) for obj in panel_objects]
                    object_ids_str = ",".join(panel_ids)
                    
                    aggregate_csv = client.get_aggregate_data(
                        system_id, start=start_date, end=end_date, 
                        level="minute", object_ids=object_ids_str, return_dataframe=False
                    )
                    
                    if aggregate_csv and aggregate_csv.strip():
                        agg_lines = aggregate_csv.strip().split('\n')
                        print(f"Sample panel data (3 panels): {agg_lines[0] if agg_lines else 'No data'}")
                        
                        if len(agg_lines) > 1:
                            sample_rows = agg_lines[1:6]  # Show first 5 rows
                            for i, line in enumerate(sample_rows, 1):
                                print(f"  {i}. {line}")
                            
                            if len(agg_lines) > 6:
                                print(f"  ... ({len(agg_lines) - 6} more panel data rows)")
                    else:
                        print("No panel-level aggregate data available")
                else:
                    print("No individual panels found for aggregate data sample")
                    
            except Exception as e:
                print(f"Could not get aggregate data sample: {e}")
            
        except Exception as e:
            print(f"{get_status_icon('warning')} Raw data sample error: {e}")
        
        # ===========================================
        # SUMMARY
        # ===========================================
        print_section("SESSION SUMMARY")
        
        print(f"{get_status_icon('success')} Successfully demonstrated:")
        print("  * System information retrieval")
        print("  * Real-time performance monitoring")
        print("  * Historical data analysis")
        print("  * System efficiency calculations")
        print("  * Panel-level performance comparison")
        print("  * Alert monitoring")
        print("  * Data export capabilities")
        
        print(f"\n{get_status_icon('info')} System '{system['name']}' appears to be operating normally")
        print(f"{get_status_icon('info')} Use the enhanced client methods for detailed analysis and monitoring")
        
        print_subsection("Logout")
        logout_result = client.logout()
        print(f"{get_status_icon('success')} Successfully logged out")
    
    print(f"\n{'='*60}")
    print("Analysis complete! Client automatically closed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{get_status_icon('error')} Error during execution: {e}")
        import traceback
        traceback.print_exc()