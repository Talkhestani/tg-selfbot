# <img src="https://media.githubusercontent.com/media/saeedtahmtan/telemoji/refs/heads/main/webp/animated/U%2B1F916_1.webp" width="28" style="vertical-align: middle;"> ربات خود تلگرام (Telegram Self-Bot)

> <a href="README.md">English</a> | فارسی


یک ربات خودکار حرفه‌ای تلگرام که روی حساب شخصی تلگرام خودتان اجرا می‌شود. این ربات مدیریت پیام‌ها، پاسخ خودکار، یکپارچه‌سازی با هوش مصنوعی، یادآوری‌ها، ابزارهای شبکه و کاربردی، تبدیل‌کننده‌ها و خودکارسازی کامل پروفایل را با معماری تمیز و قابل تست ارائه می‌دهد.

ساخته شده با Python 3.12+، Telethon، SQLAlchemy 2.x (async) روی SQLite، APScheduler، yt-dlp، httpx و pydantic.

## <img src="https://media.githubusercontent.com/media/saeedtahmtan/telemoji/refs/heads/main/webp/animated/U%2B2728_1.webp" width="24" style="vertical-align: middle;"> ویژگی‌ها

- **مدیریت پیام‌ها** — حذف پیام‌های قدیمی (بر اساس سن یا تعداد) و حذف پیام‌ها بر اساس کلمه کلیدی/regex با تقسیم ایمن و مدیریت FloodWait.
- **پاسخ خودکار** — فعال‌سازی/غیرفعال‌سازی، پاسخ پیش‌فرض ایستا و قوانین کلمه کلیدی با اولویت، خنک‌کننده، regex، تطبیق دقیق/شامل، خنک‌کننده برای هر کاربر و فیلترهای چت مجاز/مسدود.
- **یکپارچه‌سازی هوش مصنوعی** — لایه مستقل از تأمین‌کننده (سازگار با OpenAI)؛ پاسخ خودکار هوش مصنوعی با زمینه، پرامپت سفارشی، محدودیت‌های استفاده و خنک‌کننده؛ تولید بیو و نام کاربری با هوش مصنوعی.
- **یادآوری‌ها** — یک‌بار (نسبی یا تاریخ/زمان مطلق)، روزانه، هفتگی و ماهانه که پس از راه‌اندازی مجدد حفظ می‌شوند؛ لیست، حذف و به تعویق انداختن.
- **دانلودکننده** — `/dl <url>` از طریق yt-dlp با صف، پیشرفت، محدودیت اندازه/زمان، پاک‌سازی فایل موقت و بارگذاری مجدد به تلگرام.
- **ابزارهای کاربردی** — JSON (قالب‌بندی/اعتبارسنجی)، Base64، کد/رمزگشایی URL، UUID، هش‌ها، تست‌کننده regex، تایم‌استمپ/زمان یونیکس، رمزگشای JWT، کوتاه‌کننده URL، QR، بارکد، تبدیل رنگ، Markdown↔HTML، متن→QR و اسکرین‌شات URL.
- **ابزارهای شبکه** — ping، جستجوی DNS، جستجوی IP، WHOIS، وضعیت HTTP، اطلاعات گواهی SSL، آپ‌تایم و هدرها — همه با حفاظت دقیق SSRF.
- **ماشین‌حساب و زمان** — محاسبه‌گر عبارت امن (بدون `eval`)، کرنومتر، تایمر، عدد/انتخاب تصادفی، تولیدکننده رمز عبور امن.
- **تبدیل‌کننده‌ها** — واحدها، ارز (ذخیره‌شده)، منطقه زمانی در `zoneinfo`، آب‌وهوا (ذخیره‌شده)، محاسبه‌گر تاریخ، سن و BMI.
- **خودکارسازی پروفایل** — تنظیم بیو، بیو خودکار، بیوهای مبتنی بر زمان، بیو زمان فعلی (ساعت)، بیو وضعیت آنلاین، چرخش تصادفی بیو، تولید نام کاربری، تولید عکس پروفایل با هوش مصنوعی و پشتیبان‌گیری/بازیابی پروفایل با تأیید.
- **مجوزها و امنیت** — دستورات فقط برای مالک، لیست‌های چت مجاز/مسدود، مجوزهای هر دستور، تأیید برای اقدامات مخرب، محدودیت نرخ و لاگ امن بدون افشای رازها.

## <img src="https://media.githubusercontent.com/media/saeedtahmtan/telemoji/refs/heads/main/webp/animated/U%2B1F4A1_1.webp" width="24" style="vertical-align: middle;"> نیازمندی‌ها

- Python 3.12 یا جدیدتر (توسعه و آزمایش روی 3.14)
- یک حساب کاربری تلگرام با `api_id` / `api_hash` از [my.telegram.org](https://my.telegram.org)

## <img src="https://media.githubusercontent.com/media/saeedtahmtan/telemoji/refs/heads/main/webp/animated/U%2B1F4BB_1.webp" width="24" style="vertical-align: middle;"> نصب

```powershell
# ۱) ایجاد و فعال‌سازی محیط مجازی
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# ۲) نصب بسته با ابزارهای توسعه (و پشتیبانی اختیاری اسکرین‌شات)
pip install -e ".[dev,screenshot]"

# ۳) پیکربندی
Copy-Item .env.example .env
# سپس .env را ویرایش کنید و API_ID و API_HASH را پر کنید
```

در اولین ورود، ربات شماره تلفن شما و کد تأیید را می‌خواهد. یک فایل نشست تلگرام (نه رمز عبور) به‌صورت محلی ذخیره می‌شود تا وارد بمانید.

## <img src="https://media.githubusercontent.com/media/saeedtahmtan/telemoji/refs/heads/main/webp/animated/U%2B2699_1.webp" width="24" style="vertical-align: middle;"> پیکربندی

`.env.example` را به `.env` کپی کنید و حداقل این موارد را تنظیم کنید:

```env
API_ID=123456
API_HASH=abcdef0123456789abcdef0123456789
OWNER_ID=your_numeric_user_id
```

گزینه‌های مهم:

| متغیر | پیش‌فرض | توضیحات |
| --- | --- | --- |
| `API_ID` / `API_HASH` | — | اعتبارنامه‌های اپ تلگرام (ضروری) |
| `SESSION_NAME` | `selfbot` | نام فایل نشست |
| `SESSION_STRING` | خالی | رشته نشست صادرشده اختیاری |
| `OWNER_ID` | خالی | شناسه کاربری عددی شما (بررسی فقط برای مالک) |
| `COMMAND_PREFIX` | `/` | پیشوند دستور |
| `TIMEZONE` | `Asia/Tehran` | منطقه زمانی نمایش/زمان‌بندی |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/app.db` | آدرس پایگاه داده SQLAlchemy |
| `AI_PROVIDER` / `AI_API_KEY` / `AI_MODEL` | خالی | برای غیرفعال کردن هوش مصنوعی خالی بگذارید |
| `AI_API_BASE` | خالی | آدرس پایه سفارشی سازگار با OpenAI |
| `DOWNLOAD_DIR` | `downloads` | دایرکتوری خروجی yt-dlp |
| `MAX_DOWNLOAD_SIZE_MB` | `500` | حداکثر اندازه دانلود |
| `DOWNLOAD_TIMEOUT` | `300` | زمان پایان دانلود (ثانیه) |
| `WEATHER_API_KEY` | خالی | کلید اختیاری ارائه‌دهنده آب‌وهوا |
| `URL_SHORTENER_API_KEY` | خالی | کلید اختیاری ارائه‌دهنده کوتاه‌کننده URL |
| `LOG_LEVEL` | `INFO` | سطح لاگ |
| `REQUIRE_CONFIRMATION` | `true` | درخواست تأیید قبل از اقدامات مخرب/تغییرات پروفایل |

هرگز `.env` یا فایل‌های نشست را در مخزن ثبت نکنید.

## <img src="https://media.githubusercontent.com/media/saeedtahmtan/telemoji/refs/heads/main/webp/animated/U%2B26A1_1.webp" width="24" style="vertical-align: middle;"> اجرا

```powershell
python -m selfbot.app
```

اگر اعتبارنامه‌ها وجود نداشته باشد، ربات با یک پیام خطای فارسی واضح خارج می‌شود.

## <img src="https://media.githubusercontent.com/media/saeedtahmtan/telemoji/refs/heads/main/webp/animated/U%2B1F4AC_1.webp" width="24" style="vertical-align: middle;"> دستورات

دستورات را به پیام‌های خودتان (پیام‌های ذخیره‌شده) یا در چت‌هایی که ربات مجاز است ارسال کنید. همه پاسخ‌ها به فارسی هستند.

### راهنما و مجوزها

| دستور | توضیحات |
| --- | --- |
| `/help` / `/help <section>` | نمایش راهنما (مثلاً `/help reminder`، `/help network`، `/help <command>`) |
| `/owneronly on/off` | محدود کردن همه دستورات به چت‌های مالک |
| `/allowchat <chat-id>` / `/denychat <chat-id>` | افزودن/حذف چت از لیست مجاز / مسدود |
| `/allowlist` / `/chatperms` | نمایش مجوزهای چت |

### مدیریت پیام‌ها

| دستور | توضیحات |
| --- | --- |
| `/del 100` | حذف آخرین ۱۰۰ پیام چت فعلی |
| `/delold 30` / `/delold 7d` | حذف پیام‌های شما قدیمی‌تر از تعداد/مدت |
| `/delword spam,scam` / `/delword spam --limit 100` | حذف پیام‌های حاوی کلمات کلیدی (گزینه regex) |

### پاسخ خودکار و هوش مصنوعی

| دستور | توضیحات |
| --- | --- |
| `/autoreply on` / `/autoreply off` / `/autoreply set <msg>` | تغییر وضعیت و تنظیم پاسخ پیش‌فرض |
| `/arule add <keyword> => <reply>` / `/arule list` / `/arule remove <id>` | قوانین پاسخ کلمه کلیدی |
| `/ai on` / `/ai off` / `/ai setprompt <prompt>` | تغییر وضعیت و پیکربندی پاسخ خودکار هوش مصنوعی |

### یادآوری‌ها

| دستور | توضیحات |
| --- | --- |
| `/remind 20m با مشتری تماس بگیر` | یادآوری یک‌بار (نسبی) |
| `/remind 2026-10-01 18:30 جلسه` | یادآوری یک‌بار (تاریخ/زمان مطلق) |
| `/remind daily 09:00 ورزش` | یادآوری روزانه |
| `/remind weekly mon 09:00 جلسه هفتگی` | یادآوری هفتگی |
| `/remind monthly 1 10:00 پرداخت قبض` | یادآوری ماهانه |
| `/reminders` | لیست یادآوری‌ها |
| `/reminddel <id>` | حذف یادآوری |
| `/snooze <id> <duration>` | به تعویق انداختن یادآوری یک‌بار (مثلاً `/snooze 12 30m`) |

### ابزارهای کاربردی

| دستور | توضیحات |
| --- | --- |
| `/json format` / `/json validate` | قالب‌بندی/فشرده‌سازی/اعتبارسنجی JSON |
| `/b64 encode <text>` / `/b64 decode <data>` | کد/رمزگشایی Base64 |
| `/urlencode <text>` / `/urldecode <text>` | کد/رمزگشایی URL |
| `/uuid` / `/uuid 5` | تولید UUID |
| `/hash sha256 <text>` | هش MD5/SHA1/SHA256/SHA512 |
| `/regex <pattern> <text>` | تست regex: تطبیق‌ها، گروه‌ها، موقعیت‌ها |
| `/timestamp` / `/timestamp 2026-10-01 12:00` | تبدیل تایم‌استمپ |
| `/unixtime` / `/unixtime 1750000000` | زمان یونیکس فعلی/معکوس |
| `/jwt <token>` | رمزگشایی هدر/بار JWT (هرگز امضا را تأیید نمی‌کند) |
| `/short <url>` | کوتاه‌کننده URL |
| `/qr <text>` | تولید تصویر QR |
| `/textqr <text>` | متن → تصویر QR |
| `/barcode 123456789` | تولید تصویر بارکد |
| `/color <value>` | تبدیل HEX / RGB / HSL رنگ |
| `/mdhtml <text>` / `/htmlmd <html>` | تبدیل Markdown↔HTML |
| `/ss <url>` | اسکرین‌شات URL (محافظت‌شده با SSRF، قابل تنظیم نمای) |

### ابزارهای شبکه

| دستور | توضیحات |
| --- | --- |
| `/ping <host>` | بررسی تأخیر ICMP/HTTP و از دست رفتن بسته |
| `/dns <domain>` | جستجوی DNS و رکوردها |
| `/ip <host>` | جستجو و بررسی آدرس‌ها |
| `/whois <domain>` | جستجوی WHOIS |
| `/statusurl <url>` | بررسی وضعیت HTTP |
| `/ssl <host>` | اطلاعات گواهی SSL/TLS |
| `/uptime <url>` | بررسی آپ‌تایم/دسترس‌پذیری |
| `/headers <url>` | هدرهای پاسخ |

همه دستورات شبکه از طریق حفاظت SSRF اجرا می‌شوند و مقصدها به‌صورت امن جستجو می‌شوند.

### ماشین‌حساب و زمان

| دستور | توضیحات |
| --- | --- |
| `/calc 12 * (5 + 2)` | عبارت ریاضی امن |
| `/stopwatch start/stop/reset` | کرنومتر |
| `/timer 10m` / `/timer 30s` | تایمر |
| `/random 1 100` | عدد تصادفی |
| `/choose pizza,burger,pasta` | انتخاب تصادفی |
| `/password 20` | رمز عبور امن (با Python `secrets`) |

### تبدیل‌کننده‌ها

| دستور | توضیحات |
| --- | --- |
| `/convert 10 km mile` / `/convert 100 c f` | واحدها (طول، وزن، دما، زمان، اندازه داده) |
| `/currency 100 USD EUR` | تبدیل ارز (نرخ‌های ذخیره‌شده) |
| `/tz 15:00 Europe/Tehran America/New_York` | تبدیل منطقه زمانی |
| `/weather تهران` | آب‌وهوا (ذخیره‌شده) |
| `/datecalc 2026-10-01 + 30d` | محاسبه تاریخ (روز/هفته/ماه/سال) |
| `/age 2000-01-01` | محاسبه‌گر سن |
| `/bmi 180 75` | BMI از سانتی‌متر/کیلوگرم |

### خودکارسازی پروفایل

| دستور | توضیحات |
| --- | --- |
| `/bio set <text>` / `/bio list` / `/bio add <text>` / `/bio remove <id>` | مدیریت بیوها / چرخش تصادفی |
| `/bio random` | تنظیم بیو تصادفی |
| `/bio clock on/off` | بیو با زمان فعلی |
| `/bio online on/off` | بیو بر اساس وضعیت آنلاین |
| `/autobio on/off` | چرخش خودکار بیوها |
| `/biotime add 09:00-13:00 "در حال کار"` / `/biotime list` / `/biotime remove <id>` | بیوهای مبتنی بر زمان |
| `/username` / `/username 10` | تولید نام کاربری (تغییر نیاز به تأیید دارد) |
| `/profilephoto generate` / `/profilephoto set <file>` | تولید یا تنظیم عکس پروفایل |
| `/profile backup` | پشتیبان‌گیری نام/بیو/نام کاربری/عکس |
| `/profile restore <backup_id>` | بازیابی پشتیبان (نیاز به تأیید) |

## <img src="https://media.githubusercontent.com/media/saeedtahmtan/telemoji/refs/heads/main/webp/animated/U%2B1F4BB_1.webp" width="24" style="vertical-align: middle;"> توسعه

```powershell
# اجرای تست‌ها (۱۴۳ تست)
pytest -q

# بررسی کد
ruff check src tests scripts

# بررسی نوع
mypy src/selfbot --ignore-missing-imports

# تست دود آفلاین: ثبت همه دستورات بدون اتصال به تلگرام
python scripts/_smoke_test.py
```

### ساختار پروژه

```
src/selfbot/
├── app.py                    # راه‌اندازی و چرخه حیات
├── config.py                 # تنظیمات pydantic (.env)
├── services_container.py     # سیم‌کشی سرویس‌ها (تزریق وابستگی)
├── database/                 # مدل‌های SQLAlchemy async، موتور، مخازن
├── services/                 # منطق کسب‌وکار: یادآوری، پاسخ خودکار، هوش مصنوعی، شبکه و ...
├── telegram/
│   ├── client.py             # راه‌اندازی کلاینت Telethon و احراز هویت
│   ├── dispatcher.py         # ثبت دستورات، زمینه، اتصال مجوزها
│   ├── confirmation.py       # مدیریت تأیید برای اقدامات مخرب
│   └── handlers/             # مدیریت‌کننده‌های دستوری نازک تلگرام (تجربه کاربری فارسی)
├── utils/                    # ssrf، محدودیت نرخ، اعتبارسنج‌ها، لاگ
└── messages/persian.py       # رشته‌های فارسی رو به کاربر
```

## <img src="https://media.githubusercontent.com/media/saeedtahmtan/telemoji/refs/heads/main/webp/animated/U%2B1F510_1.webp" width="24" style="vertical-align: middle;"> نکات امنیتی

- حفاظت SSRF مقصدهای حلقه بازگشتی/خصوصی/پیوند محلی/نات درجه حامل و ابرداده ابری را برای همه ابزارهای شبکه مسدود می‌کند.
- ماشین‌حساب عبارات را به‌صورت امن تجزیه می‌کند و هرگز از `eval()` استفاده نمی‌کند.
- رمزهای عبور، JWTها، کلیدهای API و رشته‌های نشست هرگز لاگ نمی‌شوند؛ لاگ ساختاریافته و سانسورشده است.
- اقدامات مخرب و تغییرات پروفایل به‌صورت پیش‌فرض نیاز به تأیید فارسی (`بله`/`خیر`) دارند.
- محدودیت‌های اندازه دانلود، زمان پایان و نرخ اعمال می‌شوند.

## <img src="https://media.githubusercontent.com/media/saeedtahmtan/telemoji/refs/heads/main/webp/animated/U%2B1F4C1_1.webp" width="24" style="vertical-align: middle;"> مجوز

مجوز MIT
