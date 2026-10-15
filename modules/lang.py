"""whatsapp_controller.py üçün mətn yardımçısı (orijinal proqramdakı lang modulunun sadə əvəzi)."""
_T = {
    "status_not_found": "Nömrə tapılmadı və ya WhatsApp-da yoxdur",
    "tempo_next_grp": "Növbəti qrupa keçid: {s} san gözlənilir",
    "tempo_next_num": "Növbəti nömrəyə keçid: {s} san gözlənilir",
    "wa_chrome_error_prefix": "Chrome xətası: {err}",
    "wa_connect_failed_body": "Chrome debug rejimində açıq deyil (port 9222).",
    "wa_connect_success": "Chrome-a qoşuldu",
    "wa_general_error": "Xəta: {err}",
}


def L(key, **kw):
    t = _T.get(key, key)
    try:
        return t.format(**kw)
    except Exception:
        return t
