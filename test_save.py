from askbot.database import SessionLocal
from askbot.services.settings_store import set_setting, get_setting, SETTING_DEVELOPER_URL

with SessionLocal() as session:
    test_url = "https://test.com/" + str(hash("test"))
    print(f"Setting developer_url to {test_url}...")
    set_setting(session, SETTING_DEVELOPER_URL, test_url)
    
    # New session to verify persistence
    with SessionLocal() as session2:
        val = get_setting(session2, SETTING_DEVELOPER_URL, "default")
        print(f"Retrieved value: {val}")
        if val == test_url:
            print("SUCCESS: Setting persisted.")
        else:
            print("FAILURE: Setting did not persist.")
