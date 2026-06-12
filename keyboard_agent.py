import re
import time
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)


class KeyboardAgent:
    def __init__(self):
        self.enabled = config["keyboard"]["enabled"]
        self.typing_speed = config["keyboard"]["typing_speed"]

    def type_text(self, text):
        if not self.enabled:
            return
        try:
            import pyautogui
            pyautogui.write(text, interval=self.typing_speed)
        except ImportError:
            print("pyautogui not installed. Install with: pip install pyautogui")
        except Exception as e:
            print(f"Keyboard error: {e}")

    def press_key(self, key_combination):
        if not self.enabled:
            return
        try:
            import pyautogui
            keys = [k.strip().lower() for k in key_combination.split("+")]
            pyautogui.hotkey(*keys)
        except ImportError:
            print("pyautogui not installed.")
        except Exception as e:
            print(f"Keyboard error: {e}")

    def execute_response(self, response):
        type_match = re.search(r'\[TYPE\](.*?)(?:\[/TYPE\]|$)', response, re.DOTALL)
        key_match = re.search(r'\[KEY\](.*?)(?:\[/KEY\]|$)', response, re.DOTALL)

        if type_match:
            text_to_type = type_match.group(1).strip()
            time.sleep(1)
            self.type_text(text_to_type)

        if key_match:
            key_combo = key_match.group(1).strip()
            self.press_key(key_combo)

        clean = re.sub(r'\[/?TYPE\]|\[/?KEY\]', '', response).strip()
        return clean
