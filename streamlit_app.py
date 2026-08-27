import streamlit as st
import swisseph as swe
import datetime
import pytz
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim

# Configure Swiss Ephemeris to use Vedic Sidereal mode (Lahiri Ayanamsa)
swe.set_sid_mode(swe.SIDM_LAHIRI)

st.title("🕉️ Family Vedic Astrology Engine")
st.write("Calculate true Vedic coordinates from anywhere in the world for free.")
# List of 12 Vedic Rasis
RASIS = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", 
    "Karka (Cancer)", "Simha (Leo)", "Kanya (Virgo)", 
    "Tula (Libra)", "Vrischika (Scorpio)", "Dhanu (Sagittarius)", 
    "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
]

# Helper function to get Rasi name and remaining degrees
def get_rasi_details(total_degrees):
    # Safely extract a single numeric element if a list/tuple is passed
    if isinstance(total_degrees, (list, tuple)):
        deg = total_degrees[0]
    else:
        deg = total_degrees
        deg = deg % 360
    rasi_index = int(deg // 30)
    exact_degree = deg % 30
    return RASIS[rasi_index], exact_degree

with st.form("birth_details_form"):
    name = st.text_input("Family Member Name")
    birth_date = st.date_input("Date of Birth", datetime.date(1995, 1, 1))
    birth_time = st.time_input("Exact Time of Birth", datetime.time(12, 0))
    birth_city = st.text_input("City & Country of Birth (e.g., Bengaluru, India)")
    submitted = st.form_submit_button("Generate Full Vedic Chart")

if submitted and birth_city:
    st.subheader(f"🔮 Vedic Results for {name}")
    geolocator = Nominatim(user_agent="family_astrology_app_2026")
    try:
        # 1. Get Coordinates
        location = geolocator.geocode(birth_city)
        if not location:
            st.error("City not found. Please check spelling.")
            st.stop()
            
        lat, lon = location.latitude, location.longitude
        st.info(f"📍 Coordinates: Lat {lat:.4f}, Lon {lon:.4f}")
        
        # 2. Time Zone Correction to UTC
        tf = TimezoneFinder()                         
        timezone_str = tf.timezone_at(lng=lon, lat=lat)
        local_tz = pytz.timezone(timezone_str)
        local_dt = local_tz.localize(datetime.datetime.combine(birth_date, birth_time))
        utc_dt = local_dt.astimezone(pytz.utc)
        
        # 3. Calculate Julian Days
        year, month, day = utc_dt.year, utc_dt.month, utc_dt.day
        decimal_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        julian_day_utc = swe.julday(year, month, day, decimal_hour)
        
        # 4. CALCULATE PLANETS (Using Sidereal Lahiri Flag)
        sun_data, _ = swe.calc_ut(julian_day_utc, 0, swe.SEFLG_SIDEREAL)
        sun_rasi, sun_deg = get_rasi_details(sun_data)
        
        moon_data, _ = swe.calc_ut(julian_day_utc, 1, swe.SEFLG_SIDEREAL)
        moon_rasi, moon_deg = get_rasi_details(moon_data)
        # 5. CALCULATE ASCENDANT / LAGNA
        cusps, ascmc = swe.houses_ex(julian_day_utc, lat, lon, b'P', flags=swe.SEFLG_SIDEREAL)
        lagna_rasi, lagna_deg = get_rasi_details(ascmc)
        
        # 6. DISPLAY RESULTS IN CLEAN BLOCKS
        st.success(f"🌅 **Lagna / Ascendant:** {lagna_rasi} ({lagna_deg:.2f}°)")
        st.success(f"🌞 **Vedic Sun Sign:** {sun_rasi} ({sun_deg:.2f}°)")
        st.success(f"🌙 **Vedic Moon Sign:** {moon_rasi} ({moon_deg:.2f}°)")
        
    except Exception as e:
        st.error(f"An error occurred: {e}")
