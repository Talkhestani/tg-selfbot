"""All user-facing Persian strings, organised by feature area."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Generic
# ---------------------------------------------------------------------------
OK = "✓"
ERR = "✗"
SUCCESS = "**✓ موفق**"
ERROR = "**✗ خطا**"
CANCELED = "لغو شد"
CONFIRMED = "تأیید شد"
UNKNOWN_ERROR = "خطای غیرمنتظره‌ای رخ داد. لطفاً دوباره تلاش کنید."
NO_PERMISSION = "شما اجازه استفاده از این دستور را ندارید."
INVALID_USAGE = "نحو دستور نادرست است."
INTERNAL_ERROR = "خطایی در اجرا رخ داد. لطفاً بعداً دوباره تلاش کنید."

MSG_TOO_LONG = "پاسخ بیش از حد طولانی است و قابل ارسال نیست."
EMPTY_RESULT = "نتیجه‌ای یافت نشد."
PROCESSING = "در حال پردازش..."

CONFIRM_YES = "بله، تأیید"
CONFIRM_NO = "خیر، انصراف"

# ---------------------------------------------------------------------------
# Commands / help
# ---------------------------------------------------------------------------
HELP_HEADER = "**📚 راهنمای ربات**"
HELP_UNKNOWN_CATEGORY = "دسته‌بندی ناشناخته است."
NO_DESCRIPTION = "بدون توضیح"

# ---------------------------------------------------------------------------
# Message management
# ---------------------------------------------------------------------------
MSG_DELETED = "حذف شد"
DEL_MISSING = "تعداد پیام را وارد کنید. مثال:\n`/del 100`"
DEL_INVALID = "تعداد باید بین ۱ تا ۱۰۰۰ باشد."
DEL_STARTED = "**🧹 در حال حذف پیام‌های آخر...**"
DEL_DONE = "**🧹 {} پیام آخر حذف شد.**"
DEL_NO_MESSAGES = "پیامی برای حذف پیدا نشد."
DELOLD_INVALID = "تعداد روز معتبر نیست. مثال:\n`/delold 30` یا `/delold 7d`"
DELOLD_STARTED = "**🧹 در حال حذف پیام‌های قدیمی...**"
DELOLD_DONE = "**🧹 {} پیام قدیمی حذف شد.**"
DELOLD_NO_MESSAGES = "پیام قدیمی‌ای برای حذف پیدا نشد."
DELOLD_CONFIRM = (
    "**⚠️ آیا مطمئن هستید که می‌خواهید پیام‌های قدیمی‌تر از `{}` را حذف کنید؟**\n"
    "در صورت ادامه، **{}** پیام حذف خواهد شد."
)

DELWORD_DONE = "**🧹 {} پیام حاوی کلیدواژه حذف شد.**"
DELWORD_NO_MESSAGES = "پیامی حاوی این کلیدواژه‌ها پیدا نشد."
DELWORD_CONFIRM = (
    "**⚠️ آیا مطمئن هستید که می‌خواهید پیام‌های حاوی کلیدواژه «{}» را حذف کنید؟**"
)
DELWORD_INVALID_REGEX = "عبارت منظم (regex) نامعتبر است."

# ---------------------------------------------------------------------------
# Auto reply
# ---------------------------------------------------------------------------
AUTOREPLY_ENABLED = "**✅ پاسخ خودکار فعال شد.**"
AUTOREPLY_DISABLED = "**⛔ پاسخ خودکار غیرفعال شد.**"
AUTOREPLY_STATUS_ON = "پاسخ خودکار در حال حاضر **فعال** است."
AUTOREPLY_STATUS_OFF = "پاسخ خودکار در حال حاضر **غیرفعال** است."
AUTOREPLY_SET = "پاسخ پیش‌فرض ثبت شد."
AUTOREPLY_REPLY = "پاسخ خودکار شما:"
AUTOREPLY_NO_DEFAULT = "هنوز پاسخ پیش‌فرضی تنظیم نشده است."

RULE_ADDED = "**🎯 قانون پاسخ خودکار اضافه شد.**"
RULE_REMOVED = "قانون پاسخ خودکار حذف شد."
RULE_NOT_FOUND = "قانون با این شناسه پیدا نشد."
RULE_LIST_EMPTY = "هیچ قانون پاسخ خودکاری ثبت نشده است."
RULE_LIST_HEADER = "**🎯 قوانین پاسخ خودکار:**"

AI_ENABLED = "**✅ پاسخ هوشمند (AI) فعال شد.**"
AI_DISABLED = "**⛔ پاسخ هوشمند (AI) غیرفعال شد.**"
AI_STATUS_ON = "پاسخ هوشمند در حال حاضر **فعال** است."
AI_STATUS_OFF = "پاسخ هوشمند در حال حاضر **غیرفعال** است."
AI_NOT_CONFIGURED = (
    "پاسخ هوشمند پیکربندی نشده است.\n"
    "برای فعال‌سازی، کلید API و مدل را در فایل محیطی (`.env`) تنظیم کنید."
)
AI_PROMPT_SET = "پرامپت پاسخ هوشمند به‌روزرسانی شد."
AI_PROMPT_INVALID = "پرامپت نمی‌تواند خالی باشد."
AI_RESPONDING = "**🤖 در حال آماده‌سازی پاسخ هوشمند...**"

ALLOWED_CHATS_SET = "چت‌های مجاز به‌روزرسانی شدند."
BLOCKED_CHATS_SET = "چت‌های مسدود به‌روزرسانی شدند."
CHAT_ALREADY_ALLOWED = "این گفتگو قبلاً در لیست مجاز است."
CHAT_ALREADY_BLOCKED = "این گفتگو قبلاً در لیست مسدود است."
CHAT_UNKNOWN = "شناسه این گفتگو پیدا نشد."
CHAT_PERMS_LIST = "**🔒 فهرست دسترسی گفتگوها:**"
CHAT_PERMS_EMPTY = "هیچ دسترسی سفارشی ثبت نشده است."
CHAT_REMOVED = "دسترسی این گفتگو حذف شد."

# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------
REMINDER_CREATED = "**⏰ یادآوری با موفقیت ثبت شد.**"
REMINDER_DELETED = "**یادآوری با موفقیت حذف شد.**"
REMINDER_NOT_FOUND = "یادآوری با این شناسه پیدا نشد."
REMINDER_LIST_EMPTY = "هیچ یادآوری فعالی وجود ندارد."
REMINDER_LIST_HEADER = "**⏰ فهرست یادآوری‌ها:**"
REMINDER_SNOOZED = "**یادآوری با موفقیت به تعویق افتاد.**"
REMINDER_SNOOZE_INVALID = "مقدار تعویق نامعتبر است. مثال: `30m` یا `2h`"
REMINDER_INVALID_TIME = "زمان واردشده معتبر نیست."
REMINDER_INVALID_DAY = "روز هفته نامعتبر است. مقادیر مجاز: `mon` تا `sun`"
REMINDER_INVALID_DAY_OF_MONTH = "روز ماه باید بین ۱ تا ۲۸ باشد."
REMINDER_INVALID_DURATION = "مدت زمان واردشده معتبر نیست. مثال: `20m` یا `2h`"
REMINDER_INVALID_TYPE = "نوع یادآوری نامعتبر است."
REMINDER_PAST_TIME = "زمان واردشده در گذشته است."
REMINDER_TRIGGERED = "**⏰ یادآوری:**"

REMINDER_TYPES = {
    "one_time": "تک‌باره",
    "daily": "روزانه",
    "weekly": "هفتگی",
    "monthly": "ماهانه",
}

REMINDER_TEMPLATE = """**⏰ یادآوری با موفقیت ثبت شد.**

**📍 شناسه:** `{reminder_id}`
**📝 متن:** {text}
**🕐 زمان بعدی:** `{next_run}`
**🔄 نوع:** {kind}
"""

REMINDER_LIST_TEMPLATE = """**ⓘ `{reminder_id}`** — {text}
   نوع: {kind} | زمان: `{schedule}`"""

# ---------------------------------------------------------------------------
# Downloader
# ---------------------------------------------------------------------------
DOWNLOAD_INVALID_URL = "لینک واردشده معتبر نیست."
DOWNLOAD_STARTED = "**⏬ دانلود شروع شد. منتظر بمانید...**"
DOWNLOAD_QUEUED = "**⏳ دانلود در صف قرار گرفت.**"
DOWNLOAD_IN_PROGRESS = "یک دانلود دیگر در حال انجام است. درخواست شما در صف قرار گرفت."
DOWNLOAD_NO_URL = "لطفاً یک لینک وارد کنید. مثال:\n`/dl https://youtube.com/watch?v=...`"
DOWNLOAD_UNSUPPORTED = "این لینک توسط یوتیوب‌دانلودر پشتیبانی نمی‌شود."
DOWNLOAD_FAILED = "دانلود با خطا مواجه شد: {}"
DOWNLOAD_SIZE_EXCEEDED = "حجم فایل بیش از حد مجاز است."
DOWNLOAD_TIMEOUT = "زمان دانلود به پایان رسید."
DOWNLOAD_CANCELLED = "دانلود لغو شد."
DOWNLOAD_UPLOADING = "**⏫ در حال ارسال فایل دانلودشده...**"
DOWNLOAD_DONE = "**✅ دانلود با موفقیت انجام شد.**"
DOWNLOAD_NOT_FOUND = "دانلودی با این شناسه پیدا نشد."
DOWNLOAD_TOO_MANY = "تعداد دانلودهای در حال انتظار بیش از حد مجاز است."

# ---------------------------------------------------------------------------
# Utility tools
# ---------------------------------------------------------------------------
JSON_FORMAT_OK = "**✅ JSON با موفقیت قالب‌بندی شد.**"
JSON_VALID = "**✅ JSON معتبر است.**"
JSON_INVALID = "**❌ JSON نامعتبر است:**\n{}"
JSON_MISSING_TEXT = "متن JSON را وارد کنید. مثال:\n`/json format {\"a\": 1}`"
B64_MISSING_TEXT = "متن را وارد کنید. مثال:\n`/b64 encode Hello`"
B64_DECODE_ERROR = "متن واردشده کد Base64 معتبر نیست."
URLENC_TOO_LONG = "متن واردشده برای کدگذاری URL بیش از حد طولانی است."
UUID_INVALID_COUNT = "تعداد باید بین ۱ تا ۲۰ باشد."
UUID_HEADER = "**🆔 شناسه‌های یکتا (UUID):**"
HASH_MISSING_TEXT = "متن را وارد کنید. مثال:\n`/hash sha256 hello`"
HASH_UNSUPPORTED = "الگوریتم هش پشتیبانی نمی‌شود. گزینه‌ها: `md5`, `sha1`, `sha256`, `sha512`"
HASH_HEADER = "**🔐 مقدار هش:**"
REGEX_MISSING = "الگو و متن را وارد کنید. مثال:\n`/regex \\\\d+ hello123`"
REGEX_INVALID = "الگوی عبارت منظم نامعتبر است:\n{}"
REGEX_NO_MATCH = "عبارتی یافت نشد."
REGEX_MATCHES = "تعداد تطبیق: {}\n{}"
TIMESTAMP_NOW = "**⏱ زمان فعلی:**"
TIMESTAMP_INVALID = "زمان واردشده معتبر نیست."
TS_TO_UNIX = "مقدار یونیکس:"
TS_FROM_UNIX = "زمان معادل:"
JWT_MISSING = "توکن JWT را وارد کنید. مثال:\n`/jwt <token>`"
JWT_INVALID = "توکن JWT نامعتبر است."
JWT_DISCLAIMER = "نکته: این ابزار فقط هدر و پیلود را رمزگشایی می‌کند و صحت امضای توکن را بررسی نمی‌کند."
QR_INVALID_TEXT = "متن یا لینک را وارد کنید یا روی یک پیام ریپلای کنید. مثال:\n`/qr https://example.com`"
QR_INVALID_URL = "لینک واردشده معتبر نیست."
BARCODE_INVALID = "مقدار بارکد را وارد کنید. مثال:\n`/barcode 123456789`"
BARCODE_INVALID_VALUE = "مقدار بارکد باید فقط شامل ارقام باشد."
COLOR_INVALID = "رنگ واردشده معتبر نیست. مثال:\n`/color #ff0000` یا `/color 255,0,0`"
COLOR_RESULT = "**🎨 اطلاعات رنگ:**"
MDHTML_MISSING = "متن Markdown را وارد کنید. مثال:\n`/mdhtml **bold**`"
HTMLMD_MISSING = "متن HTML را وارد کنید. مثال:\n`/htmlmd <b>bold</b>`"
SCREENSHOT_MISSING = "لینک را وارد کنید. مثال:\n`/ss https://example.com`"
SCREENSHOT_DISABLED = (
    "ابزار اسکرین‌شات نیاز به نصب Playwright دارد.\n"
    "ابتدا آن را نصب کنید: `pip install selfbot[screenshot]` و سپس `playwright install chromium`"
)
SCREENSHOT_ERROR = "اسکرین‌شات گرفته نشد: {}"
URL_SHORTENED = "**🔗 لینک کوتاه‌شده:**"
URL_SHORTENER_UNAVAILABLE = "سرویس کوتاه‌کننده لینک در دسترس نیست."
URL_SHORTENER_INVALID_URL = "لینک واردشده معتبر نیست."
URL_SHORTENER_NOT_CONFIGURED = "کوتاه‌کننده لینک پیکربندی نشده است."

# ---------------------------------------------------------------------------
# Network tools
# ---------------------------------------------------------------------------
NET_PING_MISSING = "نام میزبان یا آدرس را وارد کنید. مثال:\n`/ping example.com`"
NET_DNS_MISSING = "نام میزبان را وارد کنید. مثال:\n`/dns example.com`"
NET_IP_MISSING = "نام میزبان یا آدرس را وارد کنید. مثال:\n`/ip example.com`"
NET_WHOIS_MISSING = "نام دامنه را وارد کنید. مثال:\n`/whois example.com`"
NET_URL_MISSING = "لینک را وارد کنید. مثال:\n`/statusurl https://example.com`"
NET_SSL_MISSING = "نام دامنه را وارد کنید. مثال:\n`/ssl example.com`"
NET_RESOLVE_ERROR = "آدرس واردشده قابل شناسایی نیست."
NET_BLOCKED = "دسترسی به این نشانی مجاز نیست (آدرس داخلی / محرمانه)."
NET_TIMEOUT = "درخواست با تأخیر مواجه شد یا سرور پاسخ نداد."
NET_ERROR = "خطا: {}"

PING_RESULT = "**🏓 نتیجه پینگ به `{host}`:**"
PING_FAILED = "پینگ انجام نشد: {}"
DNS_RESULT = "**🌐 نتایج DNS برای `{host}`:**"
DNS_NO_RECORDS = "رکوردی برای `{host}` یافت نشد."
IP_RESULT = "**📡 اطلاعات `{target}`:**"
WHOIS_RESULT = "**📋 اطلاعات WHOIS برای `{domain}`:**"
STATUS_RESULT = "**📶 وضعیت HTTP:**"
UPTIME_STATUS = "**▶️ وب‌سایت `{url}` در دسترس است.** (گذشته: {uptime})"
UPTIME_DOWN = "**⛔ وب‌سایت `{url}` در دسترس نیست.**"
SSL_RESULT = "**🔐 اطلاعات گواهی SSL برای `{host}`:**"
HEADERS_RESULT = "**📨 هدرهای `{url}`:**"

# ---------------------------------------------------------------------------
# Calculator and time utilities
# ---------------------------------------------------------------------------
CALC_MISSING = "یک عبارت ریاضی وارد کنید. مثال:\n`/calc 12 * (5 + 2)`"
CALC_INVALID = "عبارت ریاضی واردشده معتبر نیست."
CALC_ERROR = "خطا در محاسبه: {}"
CALC_ADVANCED = "برای توابع پیشرفته، تابع را با حروف انگلیسی بنویسید (مثلاً `sin`, `sqrt`)."
STOPWATCH_STARTED = "**▶️ کرنومتر شروع شد.**"
STOPWATCH_STOPPED = "**⏹ کرنومتر متوقف شد.**\n⏱ مدت: `{}`"
STOPWATCH_RESET = "کرنومتر صفر شد."
STOPWATCH_NOT_RUNNING = "کرنومتر در حال اجرا نیست."
TIMER_MISSING = "مدت را وارد کنید. مثال:\n`/timer 10m` یا `/timer 30s`"
TIMER_INVALID = "مدت زمان واردشده معتبر نیست."
TIMER_STARTED = "**⏳ تایمر `{}` تنظیم شد.**"
TIMER_FINISHED = "**⏰ تایمر تمام شد!**"
RANDOM_MISSING = "بازه را وارد کنید. مثال:\n`/random 1 100`"
RANDOM_INVALID = "بازه اعداد نامعتبر است."
RANDOM_RESULT = "**🎲 عدد تصادفی: `{}`**"
CHOOSE_MISSING = "گزینه‌ها را با کاما وارد کنید. مثال:\n`/choose pizza,pasta`"
PASSWORD_MISSING = "طول رمز عبور را وارد کنید. مثال:\n`/password 20`"
PASSWORD_INVALID = "طول رمز عبور باید بین ۸ تا ۶۴ باشد."
PASSWORD_RESULT = "**🔑 رمز عبور تولید شد:**"

# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------
CONVERT_MISSING = "مقدار و واحدها را وارد کنید. مثال:\n`/convert 10 km mile`"
CONVERT_INVALID_VALUE = "مقدار واردشده عدد معتبری نیست."
CONVERT_UNKNOWN_UNIT = "واحد پشتیبانی نمی‌شود: {}"
CONVERT_SAME_UNIT = "واحد مبدأ و مقصد یکسان است."
CONVERT_RESULT = "**✅ {} {} = {} {}**"
CONVERT_CATEGORIES = "دسته‌های پشتیبانی‌شده: **طول، وزن، دما، زمان، حجم داده**"
CURRENCY_MISSING = "مشخصات تبدیل را وارد کنید. مثال:\n`/currency 100 USD EUR`"
CURRENCY_INVALID_AMOUNT = "مقدار واردشده عدد معتبری نیست."
CURRENCY_ERROR = "تبدیل ارز انجام نشد: {}"
CURRENCY_RESULT = "**💱 {} {} = {} {}**"
CURRENCY_RATE_HINT = "نرخ: `{}` (بروزرسانی: {})"
TZ_MISSING = "زمان و منطقه زمانی را وارد کنید. مثال:\n`/tz 15:00 Europe/Tehran America/New_York`"
TZ_INVALID_TIME = "زمان واردشده معتبر نیست."
TZ_INVALID_ZONE = "منطقه زمانی «{}» معتبر نیست."
TZ_RESULT = "**🌍 زمان در مناطق مختلف:**"
WEATHER_MISSING = "نام شهر را وارد کنید. مثال:\n`/weather Tehran`"
WEATHER_ERROR = "اطلاعات آب‌وهوا دریافت نشد: {}"
WEATHER_RESULT = "**🌤 آب‌وهوای `{city}`:**"
DATEDIFF_MISSING = "تاریخ و مقدار را وارد کنید. مثال:\n`/datecalc 2026-10-01 + 30d`"
DATEDIFF_INVALID = "عبارت تاریخ واردشده معتبر نیست."
DATEDIFF_UNKNOWN_UNIT = "واحد زمان نامعتبر است. گزینه‌ها: `d`, `w`, `m`, `y`"
DATEDIFF_RESULT = "**📅 نتیجه: `{}`**"
AGE_MISSING = "تاریخ تولد را وارد کنید. مثال:\n`/age 2000-01-01`"
AGE_INVALID = "تاریخ تولد معتبر نیست."
AGE_FUTURE = "تاریخ تولد نمی‌تواند در آینده باشد."
AGE_RESULT = "**🎂 سن شما: `{}`**"
BMI_MISSING = "قد (سانتی‌متر) و وزن (کیلوگرم) را وارد کنید. مثال:\n`/bmi 180 75`"
BMI_INVALID = "قد و وزن واردشده معتبر نیستند."
BMI_RESULT = "**⚖️ شاخص توده بدنی (BMI): `{}`**"
BMI_CATEGORY = "وضعیت: {}"

# ---------------------------------------------------------------------------
# Profile automation
# ---------------------------------------------------------------------------
BIO_SET = "**✅ بیو با موفقیت تنظیم شد.**"
BIO_INVALID = "متن بیو را وارد کنید. مثال:\n`/bio set سلام!`"
BIO_TOO_LONG = "بیو نمی‌تواند بیشتر از ۷۰ کاراکتر باشد."
BIO_CLOCK_ON = "**نمایش ساعت در بیو فعال شد.**"
BIO_CLOCK_OFF = "**نمایش ساعت در بیو غیرفعال شد.**"
BIO_ONLINE_ON = "**نمایش وضعیت آنلاین در بیو فعال شد.**"
BIO_ONLINE_OFF = "**نمایش وضعیت آنلاین در بیو غیرفعال شد.**"
BIO_ONLINE_UNSUPPORTED = (
    "نمایش آنلاین بودن در بیو توسط تلگرام پشتیبانی نمی‌شود؛ "
    "این قابلیت به‌صورت خودکار پیاده‌سازی نشد."
)
BIO_RANDOM_SET = "در حال انتخاب یک بیوی تصادفی از فهرست..."
BIO_LIST_EMPTY = "هیچ بیویی ذخیره نشده است. برای افزودن: `/bio add \"متن\"`"
BIO_LIST_HEADER = "**📝 فهرست بیوها:**"
BIO_ADDED = "**بیو به فهرست افزوده شد.**"
BIO_REMOVED = "**بیو از فهرست حذف شد.**"
BIO_NOT_FOUND = "بیویی با این شناسه پیدا نشد."

AUTO_BIO_ON = "**بیوی خودکار فعال شد.**"
AUTO_BIO_OFF = "**بیوی خودکار غیرفعال شد.**"
NAMECLOCK_ON = "**🕐 ساعت زنده در نام پروفایل فعال شد.**"
NAMECLOCK_OFF = "**🕐 ساعت زنده در نام پروفایل غیرفعال شد.**"

# ---------------------------------------------------------------------------
# Help categories
# ---------------------------------------------------------------------------
HELP_CATEGORIES = {
    "main": "دستورات اصلی",
    "reminder": "یادآوری‌ها",
    "autoreply": "پاسخ خودکار",
    "message": "مدیریت پیام‌ها",
    "tools": "ابزارهای کمکی",
    "network": "ابزارهای شبکه",
    "calc": "ماشین حساب و زمان",
    "convert": "تبدیل‌ها",
    "profile": "پروفایل",
    "ai": "هوش مصنوعی",
}

HELP_MAIN = """**🤖 ربات شخصی تلگرام**

برای مشاهده راهنمای هر بخش، از `/help <بخش>` استفاده کنید.

**— دسته‌ها —**
- `/help reminder` — یادآوری‌ها
- `/help autoreply` — پاسخ خودکار
- `/help message` — مدیریت پیام‌ها
- `/help tools` — ابزارهای کمکی
- `/help network` — ابزارهای شبکه
- `/help calc` — ماشین حساب و زمان
- `/help convert` — تبدیل‌ها
- `/help profile` — پروفایل
- `/help ai` — هوش مصنوعی

⚠️ تمام دستورات با پیشوند «/» شروع می‌شوند. نتیجهٔ هر دستور روی همان پیامِ دستور نمایش داده می‌شود، پس هیچ پیام جدیدی ساخته نمی‌شود."""

HELP_REMINDER = """**⏰ یادآوری‌ها**

- `/remind 20m متن` — یادآوری تک‌باره
- `/remind 2026-10-01 18:30 متن` — یادآوری در تاریخ مشخص
- `/remind daily 09:00 متن` — یادآوری روزانه
- `/remind weekly mon 09:00 متن` — یادآوری هفتگی
- `/remind monthly 1 10:00 متن` — یادآوری ماهانه
- `/reminders` — فهرست یادآوری‌ها
- `/reminddel 12` — حذف یادآوری
- `/snooze 12 30m` — به تعویق انداختن یادآوری"""

HELP_AUTOREPLY = """**🤖 پاسخ خودکار**

- `/autoreply on` / `/autoreply off` — فعال/غیرفعال
- `/autoreply status` — وضعیت فعلی
- `/arule add کلید واژه => پاسخ` — افزودن قانون
- `/arule list` — فهرست قوانین
- `/arule remove 3` — حذف قانون
- `/owneronly on|off` — حالت مالک‌فقط
- `/allowchat <شناسه گفتگو>` — افزودن گفتگو به لیست مجاز
- `/denychat <شناسه گفتگو>` — مسدودسازی گفتگو
- `/allowlist on|off` — حالت لیست مجاز
- `/chatperms` — فهرست دسترسی گفتگوها
- `/ai on` / `/ai off` — پاسخ هوشمند (در صورت پیکربندی)
- `/ai setprompt متن` — تغییر پرامپت هوشمند"""

HELP_MESSAGE = """**🧹 مدیریت پیام‌ها**

- `/del 100` — حذف ۱۰۰ پیام آخر همین گفتگو
- `/delold 30` — حذف پیام‌های قدیمی‌تر از ۳۰ روز
- `/delold 7d` — حذف پیام‌های قدیمی‌تر از ۷ روز
- `/delword کلمه` — حذف پیام‌های حاوی کلیدواژه
- `/delword کلمه1,کلمه2 --limit 100` — با محدودیت و چند کلیدواژه
- `/dl <url> [--audio]` — دانلود محتوا (نظیر یوتیوب) و ارسال در تلگرام"""

HELP_TOOLS = """**🛠 ابزارهای کمکی**

- `/json format <json>` / `/json validate <json>` / `/json minify <json>`
- `/b64 encode <text>` / `/b64 decode <base64>`
- `/urlencode <text>` / `/urldecode <text>`
- `/uuid [count]`
- `/hash <md5|sha1|sha256|sha512> <text>`
- `/regex <pattern> <text>`
- `/timestamp [YYYY-MM-DD HH:MM]`
- `/unixtime [unix]`
- `/jwt <token>`
- `/short <url>` — کوتاه‌کردن لینک
- `/qr <text>` — ساخت کد QR
- `/barcode <digits>`
- `/color <#hex | r,g,b>`
- `/mdhtml <markdown>` — تبدیل به HTML
- `/htmlmd <html>` — تبدیل به متن
- `/textqr <text>`
- `/ss <url>` — اسکرین‌شات از لینک
- `/quote` — نقل‌قول تصادفی
- `/spam [تعداد]` — ارسال چند اسپم تصادفی"""

HELP_NETWORK = """**🌐 ابزارهای شبکه**

- `/ping example.com`
- `/dns example.com`
- `/ip example.com`
- `/whois example.com`
- `/statusurl https://example.com`
- `/ssl example.com`
- `/uptime https://example.com`
- `/headers https://example.com`"""

HELP_CALC = """**🧮 ماشین حساب و زمان**

- `/calc <expression>` — مثال: `/calc 12 * (5 + 2)`
- `/stopwatch start` / `stop` / `reset` / `status`
- `/timer 10m` — تایمر
- `/random 1 100` — عدد تصادفی
- `/choose a,b,c` — انتخاب تصادفی
- `/password 20` — رمز عبور تصادفی"""

HELP_CONVERT = """**🔄 تبدیل‌ها**

- `/convert 10 km mile` — واحدهای طول/وزن/دما/زمان/حجم داده
- `/currency` — نرخ لحظه‌ای ارز، طلا و کریپتو
- `/currency 100 USD EUR` — تبدیل ارز
- `/tz 15:00 Europe/Tehran America/New_York` — زمان در مناطق مختلف
- `/weather Tehran` — آب‌وهوا
- `/datecalc 2026-10-01 + 30d` — محاسبه تاریخ
- `/age 2000-01-01` — سن
- `/bmi 180 75` — شاخص توده بدنی"""

HELP_PROFILE = """**👤 پروفایل**

- `/bio set متن` — تنظیم بیو
- `/bio list` / `/bio add "متن"` / `/bio remove 3`
- `/bio random` — بیوی تصادفی از فهرست
- `/bio clock on|off` — نمایش ساعت در بیو
- `/bio online on|off` — نمایش وضعیت آنلاین (در صورت پشتیبانی)
- `/autobio on|off` — بیوی خودکار
- `/nameclock on|off` — نمایش ساعت زنده در نام پروفایل"""

HELP_AI = """**🤖 هوش مصنوعی**

- `/ai on` / `/ai off` — فعال یا غیرفعال‌سازی پاسخ هوشمند
- `/ai setprompt <متن>` — تنظیم پرامپت

برای فعال‌سازی، این متغیرها را در فایل `.env` تنظیم کنید:
`AI_PROVIDER`، `AI_API_KEY`، `AI_MODEL`"""

# ---------------------------------------------------------------------------
# Permission messages
# ---------------------------------------------------------------------------
PERM_OWNER_ONLY = "این دستور فقط برای مالک ربات فعال است."
PERM_BLOCKED_CHAT = "این گفتگو اجازه استفاده از این دستور را ندارد."
PERM_ALLOWED_ONLY = "این دستور فقط در گفتگوهای مجاز قابل استفاده است."
PERM_CONFIRM_TIMEOUT = "زمان تأیید به پایان رسید. عملیات لغو شد."
PERM_CONFIRM_DENIED = "عملیات توسط کاربر لغو شد."
OWNER_ONLY_ENABLED = "**حالت مالک‌فقط فعال شد.**"
OWNER_ONLY_DISABLED = "**حالت مالک‌فقط غیرفعال شد.**"
COMMAND_RATE_LIMITED = "**⏳ سرعت استفاده از این دستور زیاد است. کمی صبر کنید.**"

# ---------------------------------------------------------------------------
# Numeric / formatting
# ---------------------------------------------------------------------------
SECONDS = ["ثانیه", "دقیقه", "ساعت", "روز", "هفته"]
DURATION_LABELS = [
    ("سال", 31536000),
    ("ماه", 2592000),
    ("روز", 86400),
    ("ساعت", 3600),
    ("دقیقه", 60),
    ("ثانیه", 1),
]

WEEKDAYS_FA = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]

BMI_CATEGORIES = {
    "below": "کمبود وزن",
    "normal": "طبیعی",
    "over": "اضافه‌وزن",
    "obese": "چاقی",
}


def weekday_fa(iso_weekday: int) -> str:
    """Map a Python ISO weekday (1=Monday) to a Persian weekday name."""
    return WEEKDAYS_FA[iso_weekday - 1]


def format_duration(seconds: int) -> str:
    """Human-readable Persian duration from a number of seconds."""
    if seconds < 0:
        seconds = 0
    parts: list[str] = []
    remaining = int(seconds)
    for label, length in DURATION_LABELS:
        if remaining >= length:
            count, remaining = divmod(remaining, length)
            parts.append(f"{count} {label}")
    return " و ".join(parts) if parts else "۰ ثانیه"


def download_progress_bar(percent: float, status: str) -> str:
    """Render a text progress bar for an in-flight download."""
    stepped = max(0, min(100, int(round(percent))))
    filled = max(0, min(10, stepped // 10))
    bar = "▓" * filled + "░" * (10 - filled)
    if status == "queued":
        headline = "**⏳ در حال آماده‌سازی دانلود...**"
    elif status == "downloading":
        headline = "**⏬ در حال دانلود...**"
    elif status == "uploading":
        headline = "**⏫ در حال ارسال فایل...**"
    else:
        headline = "**⏬ دانلود...**"
    label = f"`{bar}` `{stepped}٪`"
    return f"{headline}\n\n{label}"
