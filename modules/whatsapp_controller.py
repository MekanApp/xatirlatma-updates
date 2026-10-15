"""
WhatsApp Sender - WhatsApp Web Controller v2
"""

import os, io, re, time, random, struct, pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import lang as _L

SEARCH_CSS = [
    '#side input[role="textbox"]',
    '#side div._ak9t input[role="textbox"]',
    '#side div._ak9t input',
    '#side input',
]
SEARCH_XP = [
    '//div[@id="side"]//input[@role="textbox"]',
    '//div[@id="side"]//div[contains(@class,"_ak9t")]//input',
    '//div[@id="side"]//input',
]
MSG_XP = [
    '//div[@data-tab="10"][@contenteditable="true"]',   # istifadeci terefinden tesdiqlenib
    '//div[@aria-label="Type a message"]',
    '//div[@aria-label="Mesaj yazin"]',
    '//footer//div[@contenteditable="true"]',
    '//div[@id="main"]//footer//div[@contenteditable]',
    '//div[@id="main"]//div[@role="textbox"]',
]
MSG_CSS = 'div[data-tab="10"][contenteditable="true"]'  # en etibarlı

# Emoji regex
_EMOJI_RE = re.compile(
    "["
    u"\U0001F300-\U0001F9FF"
    u"\U0001FA00-\U0001FA6F"
    u"\U0001FA70-\U0001FAFF"
    u"\U00002702-\U000027B0"
    u"\U0000200D"
    u"\U0000FE0F"
    u"\U00002640-\U00002642"
    u"\U00002600-\U00002B55"
    "]+",
    flags=re.UNICODE
)


def split_text_segments(text):
    """Mətni emoji və adi mətn seqmentlərinə ayırır."""
    segments = []
    last = 0
    for m in _EMOJI_RE.finditer(text):
        if m.start() > last:
            segments.append(('text', text[last:m.start()]))
        segments.append(('emoji', m.group()))
        last = m.end()
    if last < len(text):
        segments.append(('text', text[last:]))
    return segments


class WhatsAppController:

    def __init__(self):
        self.driver = None

    # ── Qoşulma ──────────────────────────────────────

    def connect(self):
        try:
            opts = Options()
            opts.add_experimental_option("debuggerAddress", "localhost:9222")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                svc = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=svc, options=opts)
            except Exception:
                self.driver = webdriver.Chrome(options=opts)
            return True, _L.L("wa_connect_success")
        except WebDriverException as e:
            s = str(e)
            if "9222" in s or "connection refused" in s.lower():
                return False, _L.L("wa_connect_failed_body")
            return False, _L.L("wa_chrome_error_prefix", err=s[:300])
        except Exception as e:
            return False, _L.L("wa_general_error", err=str(e)[:200])

    def disconnect(self): self.driver = None

    def is_connected(self):
        if not self.driver: return False
        try:
            _ = self.driver.current_url; return True
        except Exception:
            self.driver = None; return False

    def is_whatsapp_open(self):
        try:
            for h in self.driver.window_handles:
                self.driver.switch_to.window(h)
                if 'web.whatsapp.com' in self.driver.current_url: return True
        except Exception: pass
        return False

    def get_whatsapp_tab(self):
        try:
            for h in self.driver.window_handles:
                self.driver.switch_to.window(h)
                if 'web.whatsapp.com' in self.driver.current_url: return True
        except Exception: pass
        return False

    # ── Köməkçilər ───────────────────────────────────

    def _delay(self, a=0.5, b=1.5): time.sleep(random.uniform(a, b))

    def _find_css(self, sels, timeout=5):
        per = max(1.0, timeout / len(sels))
        for css in sels:
            try:
                el = WebDriverWait(self.driver, per).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, css)))
                if el and el.is_displayed(): return el
            except Exception: continue
        return None

    def _find_xp(self, sels, timeout=5):
        per = max(1.0, timeout / len(sels))
        for s in sels:
            try:
                el = WebDriverWait(self.driver, per).until(
                    EC.presence_of_element_located((By.XPATH, s)))
                if el and el.is_displayed(): return el
            except Exception: continue
        return None

    def _calc_wait(self, path, a=1.5, b=2.5):
        try:
            mb = os.path.getsize(path) / (1024*1024)
            return random.uniform(a, b) + min(mb * 0.8, 20.0)
        except Exception: return random.uniform(a, b)

    # ── Axtarış qutusu ───────────────────────────────

    def _focus_search(self):
        for css in SEARCH_CSS:
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, css)))
                if el and el.is_displayed():
                    self.driver.execute_script("arguments[0].click();", el)
                    self._delay(0.3, 0.5); return el
            except Exception: continue
        for xp in SEARCH_XP:
            try:
                el = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, xp)))
                if el and el.is_displayed():
                    self.driver.execute_script("arguments[0].click();", el)
                    self._delay(0.3, 0.5); return el
            except Exception: continue
        try:
            el = self.driver.execute_script(
                'var e=document.querySelector(\'#side input[role="textbox"]\');'
                'if(e){e.click();e.focus();return e;}'
                'var c=document.querySelector(\'#side div._ak9t\');'
                'if(c){var i=c.querySelector(\'input\');if(i){i.click();i.focus();return i;}}'
                'var i2=document.querySelector(\'#side input\');'
                'if(i2){i2.click();i2.focus();return i2;}return null;')
            if el: self._delay(0.3, 0.5); return el
        except Exception: pass
        return None

    def _has_results(self):
        """Axtarish neticesi var mi - span.matched-text ile yoxla."""
        try:
            els = self.driver.find_elements(By.CSS_SELECTOR, 'span.matched-text')
            return len(els) > 0
        except Exception: return False

    def _click_first_result(self):
        """Axtarishda gelen ilk qrupa klik edir."""
        try:
            # span.matched-text-in kliklenebilen atasini tap
            el = self.driver.execute_script("""
                var span = document.querySelector('span.matched-text');
                if (!span) return null;
                var el = span.parentElement;
                for (var i = 0; i < 10; i++) {
                    if (!el) break;
                    var role = el.getAttribute('role');
                    if (role === 'listitem' || role === 'button' || role === 'row') return el;
                    if (el.id && el.id.startsWith('pane')) break;
                    el = el.parentElement;
                }
                // Tapilmadisa - matched-text-in 5-ci atasi
                el = span;
                for (var j = 0; j < 5; j++) {
                    if (el.parentElement) el = el.parentElement;
                }
                return el;
            """)
            if el:
                self.driver.execute_script("arguments[0].click();", el)
                return True
        except Exception as e:
            print("click_first_result error:", e)
        return False

    def _open_group(self, group_name):
        """
        Axin:
        1. input[data-tab="3"] -> qrup adini yapisdır
        2. span.matched-text   -> gorununursemi yoxla
        3. Neticeye klik et    -> qrup acilir
        4. div[data-tab="10"]  -> mesaj qutusu aktiv oldu
        """
        try:
            # 1. Axtaris qutusunu tap ve temizle
            search = None
            try:
                search = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'input[data-tab="3"]')))
            except Exception:
                search = self._focus_search()

            if not search:
                return False, "Axtaris qutusu tapilmadi"

            self.driver.execute_script("arguments[0].value='';", search)
            search.click()
            self._delay(0.1, 0.2)
            search.send_keys(Keys.CONTROL + 'a')
            search.send_keys(Keys.DELETE)
            self._delay(0.1, 0.2)

            # 2. Qrup adini yapisdır (emoji destekli)
            pyperclip.copy(group_name)
            ActionChains(self.driver)                .key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL)                .perform()
            self._delay(1.5, 2.2)

            # 3. span.matched-text gorununursemi yoxla
            found = False
            for _ in range(3):
                try:
                    if self.driver.find_elements(By.CSS_SELECTOR, 'span.matched-text'):
                        found = True
                        break
                except Exception:
                    pass
                self._delay(0.7, 1.0)

            if not found:
                try:
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                except Exception:
                    pass
                return False, "Tapilmadi"

            # 4. Qrup tapildi - Enter bas
            search.send_keys(Keys.RETURN)
            self._delay(2.0, 3.0)

            # 5. Mesaj qutusu acildi mi yoxla
            try:
                msg = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, MSG_CSS)))
                if msg and msg.is_displayed():
                    return True, "Tapildi"
            except Exception:
                pass

            return False, "Mesaj qutusu aktivlesmedi"

        except Exception as e:
            return False, "Xeta: " + str(e)[:120]

    # ── Smart yazma (emoji + adi mətn) ───────────────

    def _type_smart(self, msg_box, text):
        """
        Mətni insan kimi yazır:
        - Adi simvollar: hərfi-hərfinə klaviatura simulyasiyası
        - Emoji: clipboard vasitəsilə yapışdırma
        - \n (yeni sətir): Shift+Enter (mesaj göndərmir, sətir keçid edir)
        """
        segs = split_text_segments(text)
        if not segs:
            return

        for kind, chunk in segs:
            if kind == 'emoji':
                pyperclip.copy(chunk)
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                self._delay(0.1, 0.2)
            else:
                # \n-i Shift+Enter ilə əvəz edərək yaz
                parts = chunk.split('\n')
                for p_idx, part in enumerate(parts):
                    for char in part:
                        msg_box.send_keys(char)
                        time.sleep(random.uniform(0.03, 0.08))
                    # Sonuncu parçadan sonra Shift+Enter YOX, aralarında var
                    if p_idx < len(parts) - 1:
                        ActionChains(self.driver)\
                            .key_down(Keys.SHIFT).send_keys(Keys.RETURN)\
                            .key_up(Keys.SHIFT).perform()
                        self._delay(0.05, 0.10)

    def _type_smart_active(self, text):
        """
        Hal-hazırda fokusda olan elementə yazır (element referansı olmadan).
        Şəkil/PDF caption-ları üçün — stale element problemini həll edir.
        \n → Shift+Enter (sətir keçid, mesaj göndərmir).
        """
        segs = split_text_segments(text)
        if not segs:
            return
        for kind, chunk in segs:
            if kind == 'emoji':
                pyperclip.copy(chunk)
                ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                self._delay(0.1, 0.2)
            else:
                parts = chunk.split('\n')
                for p_idx, part in enumerate(parts):
                    ac = ActionChains(self.driver)
                    for char in part:
                        ac.send_keys(char)
                        ac.pause(random.uniform(0.03, 0.08))
                    ac.perform()
                    if p_idx < len(parts) - 1:
                        ActionChains(self.driver)\
                            .key_down(Keys.SHIFT).send_keys(Keys.RETURN)\
                            .key_up(Keys.SHIFT).perform()
                        self._delay(0.05, 0.10)

    # ── Mətn göndər ──────────────────────────────────

    def _send_text(self, text):
        try:
            # Mesaj qutusunu tap: once CSS, sonra XPath
            box = None
            try:
                box = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, MSG_CSS)))
            except Exception:
                box = self._find_xp(MSG_XP, timeout=3)
            if not box: return False, "Mesaj qutusu tapilmadi"
            box.click()
            self._delay(0.2, 0.4)
            self._type_smart(box, text)
            self._delay(0.3, 0.6)
            box.send_keys(Keys.RETURN)
            self._delay(0.5, 1.0)
            return True, "Metn gonderildi"
        except Exception as e:
            return False, "Metn xetasi: " + str(e)[:100]

    # ── Şəkil göndər (clipboard) ─────────────────────

    def _copy_image(self, path):
        try:
            import win32clipboard
            from PIL import Image
            img = Image.open(path).convert('RGB')
            out = io.BytesIO()
            img.save(out, 'BMP')
            data = out.getvalue()[14:]
            out.close()
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            print("Image clipboard:", e); return False

    def _send_image(self, path, caption=None):
        try:
            if not os.path.isfile(path): return False, "Sekil tapilmadi"
            try:
                box = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, MSG_CSS)))
            except Exception:
                box = self._find_xp(MSG_XP, timeout=3)
            if not box: return False, "Mesaj qutusu tapilmadi"
            if not self._copy_file(path): return False, "Clipboard xetasi"
            box.click(); self._delay(0.3, 0.5)
            # Şəkil yapışdır
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            time.sleep(self._calc_wait(path, 1.5, 2.5))
            # Caption varsa: fokus dəyişmədən aktiv elementə yaz
            if caption and caption.strip():
                self._type_smart_active(caption)
                self._delay(0.2, 0.3)
            # Enter ilə göndər (element referansı lazım deyil)
            ActionChains(self.driver).send_keys(Keys.RETURN).perform()
            self._delay(1.0, 1.8)
            mb = os.path.getsize(path)/1024/1024
            return True, "Sekil gonderildi (%.1f MB)" % mb
        except Exception as e:
            return False, "Sekil xetasi: " + str(e)[:100]

    # ── Səs göndər (clipboard) ───────────────────────

    def _copy_audio(self, path):
        # Metod 1: PowerShell
        try:
            import subprocess
            r = subprocess.run(
                ['powershell', '-Command', 'Set-Clipboard -Path "%s"' % path],
                capture_output=True, timeout=10)
            if r.returncode == 0: return True
        except Exception as e: print("PS clipboard audio:", e)
        # Metod 2: CF_HDROP
        try:
            import win32clipboard, win32con
            abs_p = os.path.abspath(path)
            drop = struct.pack('IIIII', 20, 0, 0, 0, 1)
            pb = (abs_p + '\x00').encode('utf-16-le') + b'\x00\x00'
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_HDROP, drop + pb)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e: print("CF_HDROP audio:", e); return False

    def _send_audio(self, path, caption=None):
        try:
            if not os.path.isfile(path): return False, "Ses fayli tapilmadi"
            try:
                box = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, MSG_CSS)))
            except Exception:
                box = self._find_xp(MSG_XP, timeout=3)
            if not box: return False, "Mesaj qutusu tapilmadi"
            if not self._copy_audio(path): return False, "Clipboard xetasi"
            box.click(); self._delay(0.3, 0.6)
            # Səs faylı yapışdır
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            time.sleep(self._calc_wait(path, 2.0, 3.5))
            # Caption varsa: fokus dəyişmədən aktiv elementə yaz
            if caption and caption.strip():
                self._type_smart_active(caption)
                self._delay(0.2, 0.3)
            # Enter ilə göndər (element referansı lazım deyil)
            ActionChains(self.driver).send_keys(Keys.RETURN).perform()
            self._delay(1.0, 1.8)
            mb = os.path.getsize(path)/1024/1024
            return True, "Ses fayli gonderildi (%.1f MB)" % mb
        except Exception as e:
            return False, "Ses xetasi: " + str(e)[:100]

    # ── PDF göndər (clipboard) ───────────────────────

    def _copy_file(self, path):
        # Metod 1: PowerShell
        try:
            import subprocess
            r = subprocess.run(
                ['powershell', '-Command', 'Set-Clipboard -Path "%s"' % path],
                capture_output=True, timeout=10)
            if r.returncode == 0: return True
        except Exception as e: print("PS clipboard:", e)
        # Metod 2: CF_HDROP
        try:
            import win32clipboard, win32con
            abs_p = os.path.abspath(path)
            drop = struct.pack('IIIII', 20, 0, 0, 0, 1)
            pb = (abs_p + '\x00').encode('utf-16-le') + b'\x00\x00'
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_HDROP, drop + pb)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e: print("CF_HDROP:", e); return False

    def _send_pdf(self, path, caption=None):
        try:
            if not os.path.isfile(path): return False, "PDF tapilmadi"
            try:
                box = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, MSG_CSS)))
            except Exception:
                box = self._find_xp(MSG_XP, timeout=3)
            if not box: return False, "Mesaj qutusu tapilmadi"
            if not self._copy_file(path): return False, "Clipboard xetasi"
            box.click(); self._delay(0.3, 0.6)
            # PDF yapışdır
            ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            time.sleep(self._calc_wait(path, 2.0, 3.5))
            # Caption varsa: fokus dəyişmədən aktiv elementə yaz
            if caption and caption.strip():
                self._type_smart_active(caption)
                self._delay(0.2, 0.3)
            # Enter ilə göndər (element referansı lazım deyil)
            ActionChains(self.driver).send_keys(Keys.RETURN).perform()
            self._delay(1.0, 1.8)
            mb = os.path.getsize(path)/1024/1024
            return True, "PDF gonderildi (%.1f MB)" % mb
        except Exception as e:
            return False, "PDF xetasi: " + str(e)[:100]

    # ── Nömrəyə yaz ──────────────────────────────────

    def _open_number(self, phone):
        """
        1. "Yeni söhbət" düyməsinə klik → drawer açılır
        2. Drawer içindəki input[data-tab="3"]-ə nömrəni yapışdır
        3. TAPILDI:   div[data-testid="new-chat-drawer"]
                      div[data-testid="cell-frame-title"] span[dir="auto"]
           TAPILMADI: div[data-testid="search-no-results-without-keyword"]
        4. Enter → söhbət açılır
        5. MSG_CSS aktiv oldu
        VACIB: Hər iki selector drawer-ə məhdudlaşdırılıb.
               Əks halda sol söhbət siyahısındakı kontaktlar
               "tapıldı" kimi qəbul edilə bilər.
        """
        try:
            # 0. Drawer artıq açıqdırsa bağla
            try:
                d = self.driver.find_elements(
                    By.CSS_SELECTOR, 'div[data-testid="new-chat-drawer"]')
                if d and d[0].is_displayed():
                    self.driver.find_element(
                        By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    self._delay(0.5, 0.8)
            except Exception:
                pass

            # 1. "Yeni söhbət" düyməsinə klik
            opened = False
            for sel in ['span[data-testid="new-chat-outline"]',
                        'button[aria-label="Yeni söhbət"]',
                        'button[aria-label="New chat"]']:
                try:
                    el = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                    self.driver.execute_script("arguments[0].click();", el)
                    self._delay(1.0, 1.5)
                    opened = True
                    break
                except Exception:
                    continue

            # Fallback: Alt+Ctrl+N
            if not opened:
                try:
                    self.driver.find_element(By.TAG_NAME, 'body').click()
                    self._delay(0.2, 0.3)
                    ActionChains(self.driver)                        .key_down(Keys.ALT).key_down(Keys.CONTROL)                        .send_keys('n')                        .key_up(Keys.CONTROL).key_up(Keys.ALT).perform()
                    self._delay(1.0, 1.5)
                except Exception:
                    pass

            # Drawer açıldı mı yoxla
            try:
                WebDriverWait(self.driver, 4).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'div[data-testid="new-chat-drawer"]')))
            except Exception:
                return False, "Yeni sohbet drawer acilmadi"

            # 2. Drawer içindəki inputu tap
            num_input = None
            for sel in [
                'div[data-testid="new-chat-drawer"] input[data-tab="3"]',
                'div[data-testid="new-chat-drawer"] input[role="textbox"]',
                'div[data-testid="new-chat-drawer"] input[type="text"]',
            ]:
                try:
                    el = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                    if el and el.is_displayed():
                        num_input = el
                        break
                except Exception:
                    continue

            if not num_input:
                return False, "Nomre giris qutusu tapilmadi"

            # Nömrəni yapışdır
            num_input.click()
            self._delay(0.2, 0.3)
            self.driver.execute_script("arguments[0].value='';", num_input)
            num_input.send_keys(Keys.CONTROL + 'a')
            num_input.send_keys(Keys.DELETE)
            self._delay(0.1, 0.2)
            pyperclip.copy(phone)
            ActionChains(self.driver)                .key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL)                .perform()
            self._delay(2.0, 2.5)

            # 3. Tapıldı / tapılmadı yoxlaması
            # VACIB: hər iki selector DRAWER-ə məhdudlaşdırılıb
            found = False
            for _ in range(6):
                try:
                    # TAPILDI: YALNIZ drawer içindəki nəticə sayılır
                    hits = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        'div[data-testid="new-chat-drawer"] '
                        'div[data-testid="cell-frame-title"] span[dir="auto"]')
                    if hits:
                        found = True
                        break

                    # TAPILMADI: dərhal Escape, növbəti nömrəyə
                    no_res = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        'div[data-testid="search-no-results-without-keyword"]')
                    if no_res and no_res[0].is_displayed():
                        try:
                            self.driver.find_element(
                                By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                            self._delay(0.4, 0.6)
                        except Exception:
                            pass
                        return False, _L.L("status_not_found")
                except Exception:
                    pass
                self._delay(0.7, 1.0)

            if not found:
                try:
                    self.driver.find_element(
                        By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    self._delay(0.5, 0.8)
                except Exception:
                    pass
                return False, _L.L("status_not_found")

            # 4. Enter bas → söhbət açılır
            num_input.send_keys(Keys.RETURN)
            self._delay(2.0, 3.0)

            # 5. Mesaj qutusu aktifleşdimi yoxla
            try:
                msg = WebDriverWait(self.driver, 6).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, MSG_CSS)))
                if msg and msg.is_displayed():
                    return True, "Tapildi"
            except Exception:
                pass

            return False, "Mesaj qutusu aktivlesmedi"

        except Exception as e:
            return False, "Xeta: " + str(e)[:120]
    # ── Əsas göndərmə döngüsü ────────────────────────

    def send_to_groups(self, groups, send_items,
                       progress_cb=None, log_cb=None, stop_check=None):
        """
        groups: [{"name":..., ...}, ...]
        send_items: sıralanmış list of dict:
            {"type": "text"|"image"|"pdf",
             "content": str (text or file path),
             "caption": str|None (image/pdf üçün)}
        """
        total = len(groups)
        ok_count = fail_count = 0

        def log(m, s="info"):
            if log_cb: log_cb(m, s)
        def prog(i):
            if progress_cb: progress_cb(i, total, ok_count, fail_count)

        if not self.get_whatsapp_tab():
            log("WhatsApp Web tabi tapilmadi!", "error"); return 0, total

        for i, grp in enumerate(groups):
            if stop_check and stop_check():
                log("Dayandırildi.", "info"); break

            name = grp["name"] if isinstance(grp, dict) else grp
            log("Axtarilir: " + name, "info")
            found, msg = self._open_group(name)

            if not found:
                log("[X] " + name + ": " + msg, "error")
                fail_count += 1; prog(i+1); continue

            grp_ok = True
            for item in send_items:
                t = item["type"]
                content = item.get("content", "")
                caption = item.get("caption", None)

                if t == "text" and content:
                    ok, r = self._send_text(content)
                elif t == "image" and content:
                    ok, r = self._send_image(content, caption)
                elif t == "audio" and content:
                    ok, r = self._send_audio(content, caption)
                elif t == "pdf" and content:
                    ok, r = self._send_pdf(content, caption)
                else:
                    continue

                log(("[OK] " if ok else "[!] ") + name + " [" + t + "]: " + r,
                    "success" if ok else "error")
                if not ok: grp_ok = False
                self._delay(0.6, 1.2)

            if grp_ok: ok_count += 1
            else: fail_count += 1
            prog(i+1)

            if i < total - 1:
                d = random.uniform(4.0, 9.0)
                if random.random() < 0.05: d += random.uniform(12.0, 25.0)
                log(_L.L("tempo_next_grp", s=d), "info")
                dl = time.time() + d
                while time.time() < dl:
                    if stop_check and stop_check(): break
                    time.sleep(0.3)

        return ok_count, fail_count

    def send_to_numbers(self, numbers, send_items,
                        progress_cb=None, log_cb=None, stop_check=None,
                        start_from=0, status_cb=None):
        """
        numbers: list of {"phone": ...} dicts
        start_from: hansi indeksdən başla (davam etmə üçün)
        status_cb: func(index, phone, status, message)
                   status: "sent" | "failed" | "skipped"
        """
        total = len(numbers)
        ok_count = fail_count = 0

        def log(m, s="info"):
            if log_cb: log_cb(m, s)
        def prog(i):
            if progress_cb: progress_cb(i, total, ok_count, fail_count)
        def set_status(idx, phone, status, msg=""):
            if status_cb: status_cb(idx, phone, status, msg)

        if not self.get_whatsapp_tab():
            log("WhatsApp Web tabi tapilmadi!", "error"); return 0, total

        for i, item_num in enumerate(numbers):
            # Başlanğıc indeksdən əvvəlkiləri keç
            if i < start_from:
                continue

            if stop_check and stop_check():
                log("Dayandırildi.", "info"); break

            phone = item_num["phone"] if isinstance(item_num, dict) else item_num
            log("Yoxlanilir: " + phone, "info")
            found, msg = self._open_number(phone)

            if not found:
                log("[X] " + phone + ": " + msg, "error")
                set_status(i, phone, "failed", msg)
                fail_count += 1; prog(i+1); continue

            num_ok = True
            for it in send_items:
                t = it["type"]
                cnt = it.get("content", "")
                caption = it.get("caption", None)

                if t == "text" and cnt:
                    ok, r = self._send_text(cnt)
                elif t == "image" and cnt:
                    ok, r = self._send_image(cnt, caption)
                elif t == "audio" and cnt:
                    ok, r = self._send_audio(cnt, caption)
                elif t == "pdf" and cnt:
                    ok, r = self._send_pdf(cnt, caption)
                else:
                    continue

                log(("[OK] " if ok else "[!] ") + phone + " [" + t + "]: " + r,
                    "success" if ok else "error")
                if not ok: num_ok = False
                self._delay(0.6, 1.2)

            status = "sent" if num_ok else "failed"
            set_status(i, phone, status, "")
            if num_ok: ok_count += 1
            else: fail_count += 1
            prog(i+1)

            if i < total - 1:
                d = random.uniform(4.0, 9.0)
                if random.random() < 0.05: d += random.uniform(12.0, 25.0)
                log(_L.L("tempo_next_num", s=d), "info")
                dl = time.time() + d
                while time.time() < dl:
                    if stop_check and stop_check(): break
                    time.sleep(0.3)

        return ok_count, fail_count
