print = PRINT

try:
    import googletrans
except:
    print_exc()
    googletrans = None
try:
    import convobot
except:
    print_exc()
    convobot = None

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
except ImportError:
    TrOCRProcessor = None
else:
    from PIL import Image

try:
    rapidapi_key = AUTH["rapidapi_key"]
    if not rapidapi_key:
        raise
except:
    rapidapi_key = None
    print("경고:rapidapi_key를 찾을 수 없습니다.Urban Dictionary검색불가.")

try:
    from bs4 import BeautifulSoup #뷰티풀스프와 리퀘스트 임포트 해오기
    import requests
except:
    print("BeautifulSoup import error")

class Myungji_Notice(Command):
    name = ["Mj","Mjnotice", "공지사항", "공지"]
    description = "명지대학교 일반공지와 학사공지 중 하나를 택해서 최신 공지 10개를 보여주는 명령어"
    usage = "<일반공지|학사공지>"
    no_parse = True
    slash = True
    
    def __call__(self, bot, user, message, argv, **void):
        try:
            
            if argv=="일반공지" or argv=="일반" :
                create_task(message.channel.send(f'--------------------------------------일반공지--------------------------------------'))
                response = requests.get("https://www.mju.ac.kr/mjukr/255/subview.do")
                count = 6
            elif argv=="학사공지" or argv=="학사":
                create_task(message.channel.send(f'--------------------------------------학사공지--------------------------------------'))
                response = requests.get("https://www.mju.ac.kr/mjukr/257/subview.do")
                count = 12
            else:
                create_task(message.channel.send(f'일반공지 혹은 학사공지를 골라주세요! 예) ~공지사항 일반공지, ~공지사항 학사공지'))
                return
            response.encoding = 'utf-8'
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            mj_notice = soup.select('tr')
            print(mj_notice)
            for n in mj_notice[count:count+10]:
                num, title, writer, date, file, access = n.select('td')
                create_task(message.channel.send(f'```기관 : 명지대학교 공지\n제목 : {title.strong.text}\n날짜 : {date.text}```\n링크 : <https://www.mju.ac.kr{title.a["href"]}>\n--------------------------------------'))
        except:
            create_task(message.channel.send(f'{today.month}월 {today.day}일 {today.hour}시 {today.minute}분 명지대학교 오류 발생'))

class Myungji_Chatbot(Command):
    name = ["Mjchat","마루", "마루봇"]
    description = "명지대학교 마루 챗봇을 실행하주는 명령어."
    usage = "<>"
    no_parse = True
    slash = True
    
    def __call__(self, bot, user, message, argv, **void):
        try:
            create_task(message.channel.send(f'나 불렀어? 물어보고 싶은게 있으면 링크로 들어와서 물어봐!!\n링크 : <https://chatbot.mju.ac.kr/>'))
        except:
            create_task(message.channel.send(f'{today.month}월 {today.day}일 {today.hour}시 {today.minute}분 명지대학교 챗봇 오류 발생'))

class Myungji_Calender(Command):
    name = ["MjCalender","Calender","일정", "학사일정"]
    description = "명지대학교 학사일정을 보여주는 명령어"
    usage = "<>"
    no_parse = True
    slash = True
    
    def __call__(self, bot, user, message, argv, **void):
        try:
            response = requests.get("https://www.mju.ac.kr/mjukr/262/subview.do")
            response.encoding = 'utf-8'
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            mj_cal = soup.select('.list ul li')
            temp_text = "ㅡㅡㅡㅡㅡㅡㅡㅡㅡ학사일정ㅡㅡㅡㅡㅡㅡㅡㅡㅡ\n"
            for n in mj_cal:
                s = n.text.strip().replace(n.strong.text.strip(), "")
                temp_text += f"{n.strong.text.strip()} / {s.strip()}\n"
                temp_text += "ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ\n"
            create_task(message.channel.send(temp_text))
        except:
            create_task(message.channel.send(f'{today.month}월 {today.day}일 {today.hour}시 {today.minute}분 명지대학교 오류 발생'))



class Translate(Command):
    time_consuming = True
    name = ["TR", "번역"]
    description = "문자열을 다른 언어로 번역."
    usage = "<0:언어(en)>? <1:문자열>"
    flags = "v"
    no_parse = True
    rate_limit = (2, 7)
    slash = True
    if googletrans:
        languages = demap(googletrans.LANGUAGES)
        trans = googletrans.Translator()
        trans.client.headers["DNT"] = "1"

    async def __call__(self, channel, argv, user, message, **void):
        if not googletrans:
            raise RuntimeError("구글 번역을 로드할 수 없습니다.")
        if not argv:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        self.trans.client.headers["X-Forwarded-For"] = ".".join(str(xrand(1, 255)) for _ in loop(4))
        try:
            lang, arg = argv.split(None, 1)
        except ValueError:
            lang = "en"
            arg = argv
        else:
            if lang.casefold() not in self.languages:
                arg = argv
                lang = "en"
        resp = await create_future(self.trans.translate, arg, dest=lang)
        footer = dict(text=f"감지된 언어: {resp.src}")
        if getattr(resp, "pronunciation", None):
            fields = (("Pronunciation", resp.pronunciation),)
        else:
            fields = None
        self.bot.send_as_embeds(channel, resp.text, fields=fields, author=get_author(user), footer=footer, reference=message)


class Math(Command):
    _timeout_ = 4
    name = ["🔢", "M", "PY", "Sympy", "Plot", "Calc","공식평가"]
    alias = name + ["Plot3D", "Factor", "Factorise", "Factorize"]
    description = "수학 공식을 평가합니다."
    usage = "<문자열> <장황한{?v}>? <합리화{?r}>? <변수_표시{?l}>? <명확한_변수{?c}>?"
    flags = "rvlcd"
    rate_limit = (0.5, 5)
    slash = True

    async def __call__(self, bot, argv, name, message, channel, guild, flags, user, **void):
        if argv == "69":
            return py_md("69 = nice")
        if "l" in flags:
            var = bot.data.variables.get(user.id, {})
            if not var:
                return ini_md(f"{sqr_md(user)}에 대해 현재 할당된 변수가 없습니다.")
            return f"{user}에 대해 현재 할당된 변수:\n" + ini_md(iter2str(var))
        if "c" in flags or "d" in flags:
            bot.data.variables.pop(user.id, None)
            return italics(css_md(f"{sqr_md(user)}에 대한 모든 변수를 성공적으로 지웠습니다."))
        if not argv:
            raise ArgumentError(f"입력 문자열이 비어 있습니다. 도움을 위해{bot.get_prefix(guild)}수학 도움을 사용하세요.")
        r = "r" in flags
        p = flags.get("v", 0) * 2 + 1 << 7
        var = None
        if "plot" in name and not argv.lower().startswith("plot") or "factor" in name:
            argv = f"{name}({argv})"
        elif name.startswith("m"):
            for equals in ("=", ":="):
                if equals in argv:
                    ii = argv.index(equals)
                    for i, c in enumerate(argv):
                        if i >= ii:
                            temp = argv[i + len(equals):]
                            if temp.startswith("="):
                                break
                            check = argv[:i].strip().replace(" ", "")
                            if check.isnumeric():
                                break
                            var = check
                            argv = temp.strip()
                            break
                        elif not (c.isalnum() or c in " _"):
                            break
                    if var is not None:
                        break
        resp = await bot.solve_math(argv, p, r, timeout=24, variables=bot.data.variables.get(user.id))
        # Determine whether output is a direct answer or a file
        if type(resp) is dict and "file" in resp:
            await channel.trigger_typing()
            fn = resp["file"]
            f = CompatFile(fn)
            await bot.send_with_file(channel, "", f, filename=fn, best=True, reference=message)
            return
        answer = "\n".join(str(i) for i in resp)
        if var is not None:
            env = bot.data.variables.setdefault(user.id, {})
            env[var] = resp[0]
            while len(env) > 64:
                env.pop(next(iter(env)))
            bot.data.variables.update(user.id)
            return css_md(f" {sqr_md(resp[0])}로 설정된 변수 {sqr_md(var)}.")
        if argv.lower() == "help":
            return answer
        return py_md(f"{argv} = {answer}")


class UpdateVariables(Database):
    name = "variables"


class Unicode(Command):
    name = [
        "Uni2Hex", "U2H", "HexEncode",
        "Hex2Uni", "H2U", "HexDecode",
        "Uni2Bin", "U2B", "BinEncode",
        "Bin2Uni", "B2U", "BinDecode",
        "Uni2B64", "U64", "B64Encode",
        "B642Uni", "64U", "B64Decode",
        "Uni2B32", "U32", "B32Encode",
        "B322Uni", "32U", "B32Decode",
        "유니코드"
    ]
    description = "유니코드 텍스트를 16진수 또는 2진수로 변환합니다."
    usage = "<문자열>"
    no_parse = True

    def __call__(self, argv, name, **void):
        if not argv:
            raise ArgumentError("입력 문자열이 비어있습니다.")
        if name in ("uni2hex", "u2h", "hexencode"):
            b = bytes2hex(argv.encode("utf-8"))
            return fix_md(b)
        if name in ("hex2uni", "h2u", "hexdecode"):
            b = as_str(hex2bytes(to_alphanumeric(argv).replace("0x", "")))
            return fix_md(b)
        if name in ("uni2bin", "u2b", "binencode"):
            b = " ".join(f"{ord(c):08b}" for c in argv)
            return fix_md(b)
        if name in ("bin2uni", "b2u", "bindecode"):
            b = to_alphanumeric(argv).replace("0x", "").replace(" ", "").encode("ascii")
            b = (np.frombuffer(b, dtype=np.uint8) - 48).astype(bool)
            if len(b) & 7:
                a = np.zeros(8 - len(b) % 8, dtype=bool)
                if len(b) < 8:
                    b = np.append(a, b)
                else:
                    b = np.append(b, a)
            a = np.zeros(len(b) >> 3, dtype=np.uint8)
            for i in range(8):
                c = b[i::8]
                if i < 7:
                    c = c.astype(np.uint8)
                    c <<= 7 - i
                a += c
            b = as_str(a.tobytes())
            return fix_md(b)
        if name in ("uni2b64", "u64", "b64encode"):
            b = as_str(base64.b64encode(argv.encode("utf-8")).rstrip(b"="))
            return fix_md(b)
        if name in ("b642uni", "64u", "b64decode"):
            b = unicode_prune(argv).encode("utf-8") + b"=="
            if (len(b) - 1) & 3 == 0:
                b += b"="
            b = as_str(base64.b64decode(b))
            return fix_md(b)
        if name in ("uni2b32", "u32", "b32encode"):
            b = as_str(base64.b32encode(argv.encode("utf-8")).rstrip(b"="))
            return fix_md(b)
        if name in ("b322uni", "32u", "b32decode"):
            b = unicode_prune(argv).encode("utf-8")
            if len(b) & 7:
                b += b"=" * (8 - len(b) % 8)
            b = as_str(base64.b32decode(b))
            return fix_md(b)
        b = shash(argv)
        return fix_md(b)


class ID2Time(Command):
    name = ["I2T", "CreateTime", "Timestamp", "Time2ID", "T2I", "시간변환"]
    description = "Discord ID를 해당 UTC시간을 변환합니다."
    usage = "<문자열>"

    def __call__(self, argv, name, **void):
        if not argv:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        if name in ("time2id", "t2i"):
            argv = tzparse(argv)
            s = time_snowflake(argv)
        else:
            argv = int(verify_id("".join(c for c in argv if c.isnumeric() or c == "-")))
            s = snowflake_time(argv)
        return fix_md(s)


class Fancy(Command):
    name = ["FancyText", "멋진문자"]
    description = "유니코드 글꼴을 사용하여 문자열 번역을 생성합니다."
    usage = "<문자열>"
    no_parse = True
    slash = True

    def __call__(self, channel, argv, message, **void):
        if not argv:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        fields = deque()
        for i in range(len(UNIFMTS) - 1):
            s = uni_str(argv, i)
            if i == len(UNIFMTS) - 2:
                s = s[::-1]
            fields.append((f"Font {i + 1}", s + "\n"))
        self.bot.send_as_embeds(channel, fields=fields, author=dict(name=lim_str(argv, 256)), reference=message)


class Zalgo(Command):
    name = ["Chaos", "ZalgoText", "복잡서식문자"]
    description = "문자열의 문자 사이에 임의의 결합 강조 기호를 생성합니다."
    usage = "<문자열>"
    no_parse = True
    slash = True
    chrs = [chr(n) for n in zalgo_map]
    randz = lambda self: choice(self.chrs)
    def zalgo(self, s, x):
        if unfont(s) == s:
            return "".join(c + self.randz() for c in s)
        return s[0] + "".join("".join(self.randz() + "\u200b" for i in range(x + 1 >> 1)) + c + "\u200a" + "".join(self.randz() + "\u200b" for i in range(x >> 1)) for c in s[1:])

    async def __call__(self, channel, argv, message, **void):
        if not argv:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        fields = deque()
        for i in range(1, 9):
            s = self.zalgo(argv, i)
            fields.append((f"Level {i}", s + "\n"))
        self.bot.send_as_embeds(channel, fields=fields, author=dict(name=lim_str(argv, 256)), reference=message)


class Format(Command):
    name = ["FormatText" , "깔끔서식문자"]
    description = "유니코드 문자 조합을 사용하여 깔끔하게 서식이 지정된 텍스트를 생성합니다."
    usage = "<문자열>"
    no_parse = True
    slash = True
    formats = "".join(chr(i) for i in (0x30a, 0x325, 0x303, 0x330, 0x30c, 0x32d, 0x33d, 0x353, 0x35b, 0x20f0))

    def __call__(self, channel, argv, message, **void):
        if not argv:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        fields = deque()
        for i, f in enumerate(self.formats):
            s = "".join(c + f for c in argv)
            fields.append((f"Format {i}", s + "\n"))
        s = "".join("_" if c in " _" else c if c in "gjpqy" else c + chr(818) for c in argv)
        fields.append((f"Format {i + 1}", s))
        self.bot.send_as_embeds(channel, fields=fields, author=dict(name=lim_str(argv, 256)), reference=message)


class UnFancy(Command):
    name = ["UnFormat", "UnZalgo", "서식제거"]
    description = "입력된 텍스트에서 유니코드 서식 및 분음 부호를 제거합니다."
    usage = "<문자열>"
    slash = True

    def __call__(self, argv, **void):
        if not argv:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        return fix_md(argv)


class OwOify(Command):
    omap = {
        "r": "w",
        "R": "W",
        "l": "w",
        "L": "W",
    }
    otrans = "".maketrans(omap)
    name = ["UwU", "OwO", "UwUify"]
    description = "문자열에 owo/uwu텍스트 필터를 적용합니다."
    usage = "<string> <aggressive{?a}>? <basic{?b}>?"
    flags = "ab"
    no_parse = True

    def __call__(self, argv, flags, **void):
        if not argv:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        out = argv.translate(self.otrans)
        temp = None
        if "a" in flags:
            out = out.replace("v", "w").replace("V", "W")
        if "a" in flags or "b" not in flags:
            temp = list(out)
            for i, c in enumerate(out):
                if i > 0 and c in "yY" and out[i - 1].casefold() not in "aeioucdhvwy \n\t":
                    if c.isupper():
                        temp[i] = "W" + c.casefold()
                    else:
                        temp[i] = "w" + c
                if i < len(out) - 1 and c in "nN" and out[i + 1].casefold() in "aeiou":
                    temp[i] = c + "y"
            if "a" in flags and "b" not in flags:
                out = "".join(temp)
                temp = list(out)
                for i, c in enumerate(out):
                    if i > 0 and c.casefold() in "aeiou" and out[i - 1].casefold() not in "aeioucdhvwy \n\t":
                        if c.isupper():
                            temp[i] = "W" + c.casefold()
                        else:
                            temp[i] = "w" + c
        if temp is not None:
            out = "".join(temp)
            if "a" in flags:
                for c in " \n\t":
                    if c in out:
                        spl = out.split(c)
                        for i, w in enumerate(spl):
                            if w.casefold().startswith("th"):
                                spl[i] = ("D" if w[0].isupper() else "d") + w[2:]
                            elif "th" in w:
                                spl[i] = w.replace("th", "ff")
                        out = c.join(spl)
        return fix_md(out)


class AltCaps(Command):
    description = "문자열에 있는 문자의 대문자를 번갈아 사용합니다."
    usage = "<문자열>"
    no_parse = True

    def __call__(self, argv, **void):
        if not argv:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        i = argv[0].isupper()
        a = argv[i::2].casefold()
        b = argv[1 - i::2].upper()
        if i:
            a, b = b, a
        if len(a) > len(b):
            c = a[-1]
            a = a[:-1]
        else:
            c = ""
        return fix_md("".join(i[0] + i[1] for i in zip(a, b)) + c)


class Say(Command):
    description = "사용자가 제공하는 메시지를 반복합니다."
    usage = "<문자열>"
    no_parse = True
    slash = True
    
    def __call__(self, bot, user, message, argv, **void):
        create_task(bot.silent_delete(message, no_log=-1))
        if not argv:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        if not bot.is_owner(user):
            argv = lim_str("\u200b" + escape_roles(argv).lstrip("\u200b"), 2000)
        create_task(message.channel.send(argv))


# Char2Emoj, a simple script to convert a string into a block of text
def _c2e(string, em1, em2):
    chars = {
        " ": [0, 0, 0, 0, 0],
        "_": [0, 0, 0, 0, 7],
        "!": [2, 2, 2, 0, 2],
        '"': [5, 5, 0, 0, 0],
        ":": [0, 2, 0, 2, 0],
        ";": [0, 2, 0, 2, 4],
        "~": [0, 5, 7, 2, 0],
        "#": [10, 31, 10, 31, 10],
        "$": [7, 10, 6, 5, 14],
        "?": [6, 1, 2, 0, 2],
        "%": [5, 1, 2, 4, 5],
        "&": [4, 10, 4, 10, 7],
        "'": [2, 2, 0, 0, 0],
        "(": [2, 4, 4, 4, 2],
        ")": [2, 1, 1, 1, 2],
        "[": [6, 4, 4, 4, 6],
        "]": [3, 1, 1, 1, 3],
        "|": [2, 2, 2, 2, 2],
        "*": [21, 14, 4, 14, 21],
        "+": [0, 2, 7, 2, 0],
        "=": [0, 7, 0, 7, 0],
        ",": [0, 0, 3, 3, 4],
        "-": [0, 0, 7, 0, 0],
        ".": [0, 0, 3, 3, 0],
        "/": [1, 1, 2, 4, 4],
        "\\": [4, 4, 2, 1, 1],
        "@": [14, 17, 17, 17, 14],
        "0": [7, 5, 5, 5, 7],
        "1": [3, 1, 1, 1, 1],
        "2": [7, 1, 7, 4, 7],
        "3": [7, 1, 7, 1, 7],
        "4": [5, 5, 7, 1, 1],
        "5": [7, 4, 7, 1, 7],
        "6": [7, 4, 7, 5, 7],
        "7": [7, 5, 1, 1, 1],
        "8": [7, 5, 7, 5, 7],
        "9": [7, 5, 7, 1, 7],
        "A": [2, 5, 7, 5, 5],
        "B": [6, 5, 7, 5, 6],
        "C": [3, 4, 4, 4, 3],
        "D": [6, 5, 5, 5, 6],
        "E": [7, 4, 7, 4, 7],
        "F": [7, 4, 7, 4, 4],
        "G": [7, 4, 5, 5, 7],
        "H": [5, 5, 7, 5, 5],
        "I": [7, 2, 2, 2, 7],
        "J": [7, 1, 1, 5, 7],
        "K": [5, 5, 6, 5, 5],
        "L": [4, 4, 4, 4, 7],
        "M": [17, 27, 21, 17, 17],
        "N": [9, 13, 15, 11, 9],
        "O": [2, 5, 5, 5, 2],
        "P": [7, 5, 7, 4, 4],
        "Q": [4, 10, 10, 10, 5],
        "R": [6, 5, 7, 6, 5],
        "S": [3, 4, 7, 1, 6],
        "T": [7, 2, 2, 2, 2],
        "U": [5, 5, 5, 5, 7],
        "V": [5, 5, 5, 5, 2],
        "W": [17, 17, 21, 21, 10],
        "X": [5, 5, 2, 5, 5],
        "Y": [5, 5, 2, 2, 2],
        "Z": [7, 1, 2, 4, 7],
    }
    # I don't quite remember how this algorithm worked lol
    printed = ["\u200b"] * 7
    string = string.upper()
    for i in range(len(string)):
        curr = string[i]
        data = chars.get(curr, [15] * 5)
        size = max(1, max(data))
        lim = max(2, int(log(size, 2))) + 1
        printed[0] += em2 * (lim + 1)
        printed[6] += em2 * (lim + 1)
        if len(data) == 5:
            for y in range(5):
                printed[y + 1] += em2
                for p in range(lim):
                    if data[y] & (1 << (lim - 1 - p)):
                        printed[y + 1] += em1
                    else:
                        printed[y + 1] += em2
        for x in range(len(printed)):
            printed[x] += em2
    return printed


class Char2Emoji(Command):
    name = ["C2E", "Char2Emoj", "이모티콘 블록"]
    description = "문자열을 사용하여 이모티콘 블록 만들기."
    usage = "<0:문자열> <1:e이모티콘_1> <2:이모티콘_2>"
    no_parse = True
    slash = True

    def __call__(self, args, guild, message, **extra):
        if len(args) != 3:
            raise ArgumentError(
                "이 명령에는 정확히 3개의 인수가 필요합니다.\n"
                + "필요에 따라 공백이 포함된 인수를 따옴표로 묶습니다."
            )
        webhook = not getattr(guild, "ghost", None)
        for i, a in enumerate(args):
            e_id = None
            if find_emojis(a):
                e_id = a.rsplit(":", 1)[-1].rstrip(">")
                ani = a.startswith("<a:")
            elif a.isnumeric():
                e_id = a = int(a)
                try:
                    a = self.bot.cache.emojis[a]
                except KeyError:
                    ani = False
                else:
                    ani = a.animated
            if e_id:
                # if int(e_id) not in (e.id for e in guild.emojis):
                #     webhook = False
                if ani:
                    args[i] = f"<a:_:{e_id}>"
                else:
                    args[i] = f"<:_:{e_id}>"
        resp = _c2e(*args[:3])
        if hasattr(message, "simulated"):
            return resp
        out = []
        for line in resp:
            if not out or len(out[-1]) + len(line) + 1 > 2000:
                out.append(line)
            else:
                out[-1] += "\n" + line
        if len(out) <= 3:
            out = ["\n".join(i) for i in (resp[:2], resp[2:5], resp[5:])]
        if webhook:
            out = alist(out)
        return out


class EmojiCrypt(Command):
    name = ["EncryptEmoji", "DecryptEmoji", "EmojiEncrypt", "EmojiDecrypt", "암호화"]
    description = "입력 텍스트 또는 파일을 스마일리로 암호화합니다."
    usage = "<문자열> <암호화하다{?e}|해독하다{?d}> <암호화된{?p}>? <-1:비밀번호>"
    no_parse = True
    slash = True
    flags = "ed"

    async def __call__(self, args, name, flags, message, **extra):
        password = None
        for flag in ("+p", "-p", "?p"):
            try:
                i = args.index(flag)
            except ValueError:
                continue
            password = args[i + 1]
            args = args[:i] + args[i + 2:]
        msg = " ".join(args)
        fi = f"cache/temp-{ts_us()}"
        if not msg:
            msg = message.attachments[0].url
        if is_url(msg):
            msg = await self.bot.follow_url(msg, allow=True, limit=1)
            args = (python, "downloader.py", msg, "../" + fi)
            proc = await asyncio.create_subprocess_exec(*args, cwd="misc")
            try:
                await asyncio.wait_for(proc.wait(), timeout=48)
            except (T0, T1, T2):
                with tracebacksuppressor:
                    force_kill(proc)
                raise
        else:
            with open(fi, "w", encoding="utf-8") as f:
                await create_future(f.write, msg)
        fs = os.path.getsize(fi)
        args = [python, "neutrino.py", "-y", "../" + fi, "../" + fi + "-"]
        if "d" in flags or "decrypt" in name:
            args.append("--decrypt")
        else:
            c = round_random(27 - math.log(fs, 2))
            c = max(min(c, 9), 0)
            args.extend((f"-c{c}", "--encrypt"))
        args.append(password or "\x7f")
        proc = await asyncio.create_subprocess_exec(*args, cwd="misc")
        try:
            await asyncio.wait_for(proc.wait(), timeout=60)
        except (T0, T1, T2):
            with tracebacksuppressor:
                force_kill(proc)
            raise
        fn = "message.txt"
        f = CompatFile(fi + "-", filename=fn)
        return dict(file=f, filename=fn)


class Time(Command):
    name = ["🕰️", "⏰", "⏲️", "UTC", "GMT", "T", "EstimateTime", "EstimateTimezone", "시간"]
    description = "특정 GMT/UTC오프셋의 현재 시간 또는 사용자의 현재 시간을 표시합니다.<WEBSERVER>/시간을 꼭 확인하세요!"
    usage = "<오프셋_시간|사용자>?"
    slash = True

    async def __call__(self, name, channel, guild, argv, args, user, **void):
        u = user
        s = 0
        # Only check for timezones if the command was called with alias "estimate_time", "estimate_timezone", "t", or "time"
        if "estimate" in name:
            if argv:
                try:
                    if not argv.isnumeric():
                        raise KeyError
                    user = self.bot.cache.guilds[int(argv)]
                except KeyError:
                    try:
                        user = self.bot.cache.channels[verify_id(argv)]
                    except KeyError:
                        user = await self.bot.fetch_user_member(argv, guild)
            argv = None
        if args and name in "time":
            try:
                i = None
                with suppress(ValueError):
                    i = argv.index("-")
                with suppress(ValueError):
                    j = argv.index("+")
                    if i is None:
                        i = j
                    else:
                        i = min(i, j)
                if i is not None:
                    s = as_timezone(argv[:i])
                    argv = argv[i:]
                else:
                    s = as_timezone(argv)
                    argv = "0"
            except KeyError:
                user = await self.bot.fetch_user_member(argv, guild)
                argv = None
        elif name in TIMEZONES:
            s = TIMEZONES.get(name, 0)
        estimated = None
        if argv:
            h = await self.bot.eval_math(argv)
        elif "estimate" in name:
            if is_channel(user):
                h = self.bot.data.users.estimate_timezone("#" + str(user.id))
            else:
                h = self.bot.data.users.estimate_timezone(user.id)
            estimated = True
        elif name in "time":
            h = self.bot.data.users.get_timezone(user.id)
            if h is None:
                h = self.bot.data.users.estimate_timezone(user.id)
                estimated = True
            else:
                estimated = False
        else:
            h = 0
        hrs = round_min(h + s / 3600)
        if hrs:
            if abs(hrs) > 17531640:
                t = utc_ddt()
                t += hrs * 3600
            else:
                t = utc_dt()
                t += datetime.timedelta(hours=hrs)
        else:
            t = utc_dt()
        if hrs >= 0:
            hrs = "+" + str(hrs)
        out = f"UTC/GMT{hrs}의 현재 시간: {sqr_md(t)}."
        if estimated:
            out += f"\n{sqr_md(user)}의 discord 활동에서 자동으로 추정되는 시간대 사용."
        elif estimated is not None:
            out += f"\n{sqr_md(user)}에서 할당한 시간대 사용."
        return ini_md(out)


class Timezone(Command):
    description = "특정 시간대의 현재 시간을 표시합니다. <WEBSERVER>/시간을 꼭 확인하세요!"
    usage = "<표준시간대> <목록{?l}>?"

    async def __call__(self, channel, argv, message, **void):
        if not argv:
            return await self.bot.commands.time[0]("timezone", channel, channel.guild, "", [], message.author)
        if argv.startswith("-l") or argv.startswith("list"):
            fields = deque()
            for k, v in COUNTRIES.items():
                fields.append((k, ", ".join(v), False))
            self.bot.send_as_embeds(channel, description=f"[시간대를 찾으려면 여기를 클릭하십시오.]({self.bot.webserver}/time)", title="Timezone list", fields=fields, author=get_author(self.bot.user), reference=message)
            return
        secs = as_timezone(argv)
        t = utc_dt() + datetime.timedelta(seconds=secs)
        h = round_min(secs / 3600)
        if not h < 0:
            h = "+" + str(h)
        return ini_md(f"UTC/GMT{h}의 현재 시간: {sqr_md(t)}.")


class TimeCalc(Command):
    name = ["TimeDifference", "TimeDiff", "TimeSum", "TimeAdd", "시간계산"]
    description = "두 시간 사이의 합이나 차이 또는 datetime문자열의 Unix타임스탬프를 계산합니다."
    usage = "<0:시간1> [|,] <1:시간2>?"
    no_parse = True

    def __call__(self, argv, user, name, **void):
        if not argv:
            timestamps = [utc()]
        else:
            if "|" in argv:
                spl = argv.split("|")
            elif "," in argv:
                spl = argv.split(",")
            else:
                spl = [argv]
            timestamps = [utc_ts(tzparse(t)) for t in spl]
        if len(timestamps) == 1:
            out = f"{round_min(timestamps[0])} ({DynamicDT.utcfromtimestamp(timestamps[0])} UTC)"
        elif "sum" not in name and "add" not in name:
            out = dyn_time_diff(max(timestamps), min(timestamps))
        else:
            out = time_sum(*timestamps)
        return code_md(out)


class Identify(Command):
    name = ["📂", "Magic", "Mime", "FileType", "식별"]
    description = "유형,MIME 및 선택적으로 입력 파일의 세부 정보를 감지합니다."
    usage = "<url>*"
    rate_limit = (2, 7)
    mime = magic.Magic(mime=True, mime_encoding=True)
    msgcmd = True
    slash = True

    def probe(self, url):
        command = ["./ffprobe", "-hide_banner", url]
        resp = None
        for _ in loop(3):
            try:
                proc = psutil.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                fut = create_future_ex(proc.communicate, timeout=12)
                res = fut.result(timeout=12)
                resp = b"\n".join(res)
                break
            except:
                with suppress():
                    force_kill(proc)
                print_exc()
        if not resp:
            raise RuntimeError
        return as_str(resp)

    def identify(self, url):
        out = deque()
        with reqs.next().get(url, headers=Request.header(), stream=True) as resp:
            head = fcdict(resp.headers)
            it = resp.iter_content(262144)
            data = next(it)
        out.append(code_md(magic.from_buffer(data)))
        mimedata = self.mime.from_buffer(data).replace("; ", "\n")
        mime = mimedata.split("\n", 1)[0].split("/", 1)
        if mime == ["text", "plain"]:
            if "Content-Type" in head:
                ctype = head["Content-Type"]
                spl = ctype.split("/")
                if spl[-1].casefold() != "octet-stream":
                    mimedata = ctype + "\n" + mimedata.split("\n", 1)[-1]
                    mime = spl
        mimedata = "Mime유형: " + mimedata
        if "Content-Length" in head:
            fs = head['Content-Length']
        elif len(data) < 131072:
            fs = len(data)
        else:
            fs = None
        if fs is not None:
            mimedata = f"filesize: {byte_scale(int(fs))}B\n" + mimedata
        out.append(fix_md(mimedata))
        with tracebacksuppressor:
            resp = self.probe(url)
            if mime[0] == "image" and mime[1] != "gif":
                search = "Video:"
                spl = regexp(r"\([^)]+\)").sub("", resp[resp.index(search) + len(search):].split("\n", 1)[0].strip()).strip().split(", ")
                out.append(code_md(f"Codec: {spl[1]}\nSize: {spl[2].split(None, 1)[0]}"))
            elif mime[0] == "video" or mime[1] == "gif":
                search = "Duration:"
                resp = resp[resp.index(search) + len(search):]
                dur = time_disp(time_parse(resp[:resp.index(",")]), False)
                search = "bitrate:"
                resp = resp[resp.index(search) + len(search):]
                bps = resp.split("\n", 1)[0].strip().rstrip("b/s").casefold()
                mult = 1
                if bps.endswith("k"):
                    mult = 10 ** 3
                elif bps.endswith("m"):
                    mult = 10 ** 6
                elif bps.endswith("g"):
                    mult = 10 ** 9
                bps = byte_scale(int(bps.split(None, 1)[0]) * mult, ratio=1000) + "bps"
                s = f"지속기간: {dur}\n비트 전송속도: {bps}"
                search = "Video:"
                try:
                    resp = resp[resp.index(search) + len(search):]
                except ValueError:
                    pass
                else:
                    spl = regexp(r"\([^)]+\)").sub("", resp.split("\n", 1)[0].strip()).strip().split(", ")
                    s += f"\n코덱: {spl[1]}\n크기: {spl[2].split(None, 1)[0]}"
                    for i in spl[3:]:
                        if i.endswith(" fps"):
                            s += f"\nFPS: {i[:-4]}"
                            break
                out.append(code_md(s))
                search = "Audio:"
                try:
                    resp = resp[resp.index(search) + len(search):]
                except ValueError:
                    pass
                else:
                    spl = regexp(r"\([^)]+\)").sub("", resp.split("\n", 1)[0].strip()).strip().split(", ")
                    fmt = spl[0]
                    sr = spl[1].split(None, 1)[0]
                    s = f"오디오 형식: {fmt}\n오디오 샘플 속도: {sr}"
                    if len(spl) > 2:
                        s += f"\n오디오 채널: {spl[2]}"
                        if len(spl) > 4:
                            bps = spl[4].rstrip("b/s").casefold()
                            mult = 1
                            if bps.endswith("k"):
                                mult = 10 ** 3
                            elif bps.endswith("m"):
                                mult = 10 ** 6
                            elif bps.endswith("g"):
                                mult = 10 ** 9
                            bps = byte_scale(int(bps.split(None, 1)[0]) * mult, ratio=1000) + "bps"
                            s += f"\n오디오 비트 전송속도: {bps}"
                    out.append(code_md(s))
            elif mime[0] == "audio":
                search = "Duration:"
                resp = resp[resp.index(search) + len(search):]
                dur = time_disp(time_parse(resp[:resp.index(",")]), False)
                search = "Audio:"
                spl = regexp(r"\([^)]+\)").sub("", resp[resp.index(search) + len(search):].split("\n", 1)[0].strip()).strip().split(", ")
                s = f"지속기간: {dur}\n형식: {spl[0]}\n샘플 속도: {spl[1].split(None, 1)[0]}"
                if len(spl) > 2:
                    s += f"\n채널: {spl[2]}"
                    if len(spl) > 4:
                        bps = spl[4].rstrip("b/s").casefold()
                        mult = 1
                        if bps.endswith("k"):
                            mult = 10 ** 3
                        elif bps.endswith("m"):
                            mult = 10 ** 6
                        elif bps.endswith("g"):
                            mult = 10 ** 9
                        bps = byte_scale(int(bps.split(None, 1)[0]) * mult, ratio=1000) + "bps"
                        s += f"\n비트 전송속도: {bps}"
                out.append(code_md(s))
        return "".join(out)

    async def __call__(self, bot, channel, argv, user, message, **void):
        argv += " ".join(best_url(a) for a in message.attachments)
        urls = await bot.follow_url(argv, allow=True, images=False)
        if not urls:
            async for m2 in self.bot.history(message.channel, limit=5, before=message.id):
                argv = m2.content + " ".join(best_url(a) for a in m2.attachments)
                urls = await bot.follow_url(argv, allow=True, images=False)
                if urls:
                    break
        urls = set(urls)
        names = [url.rsplit("/", 1)[-1].rsplit("?", 1)[0] for url in urls]
        futs = [create_future(self.identify, url) for url in urls]
        fields = deque()
        for name, fut in zip(names, futs):
            resp = await fut
            fields.append((escape_markdown(name), resp))
        if not fields:
            raise FileNotFoundError("URL또는 첨부파일로 파일을 입력해주세요.")
        title = f"{len(fields)} 파일{'s' if len(fields) != 1 else ''} 식별됨"
        await bot.send_as_embeds(channel, title=title, author=get_author(user), fields=sorted(fields))


class Follow(Command):
    name = ["🚶", "Follow_URL", "Redirect", "찾기"]
    description = "불일치 메시지 링크를 따르거나 문자열에서 URL을 찾습니다."
    usage = "<url>*"
    rate_limit = (1, 5)
    slash = True

    async def __call__(self, bot, channel, argv, message, **void):
        urls = find_urls(argv)
        if len(urls) == 1 and is_discord_message_link(urls[0]):
            spl = argv.rsplit("/", 2)
            channel = await bot.fetch_channel(spl[-2])
            msg = await bot.fetch_message(spl[-1], channel)
            argv = msg.content
            urls = find_urls(argv)
        out = set()
        for url in urls:
            if is_discord_message_link(url):
                temp = await self.bot.follow_url(url, allow=True)
            else:
                data = await self.bot.get_request(url)
                temp = find_urls(as_str(data))
            out.update(temp)
        if not out:
            raise FileNotFoundError("유효한 URL이 감지되지 않았습니다.")
        output = f"`감지된 {len(out)} url{'s' if len(out) != 1 else ''}:`\n" + "\n".join(out)
        if len(output) > 2000 and len(output) < 54000:
            self.bot.send_as_embeds(channel, output, reference=message)
        else:
            return escape_roles(output)


class Match(Command):
    name = ["RE", "RegEx", "RexExp", "GREP", "일치"]
    description = "Linux스타일 RegExp를 사용하여 두 문자열을 일치시키거나 두 문자열의 일치 비율을 계산합니다."
    usage = "<0:문자열1> <1:문자열2>?"
    rate_limit = (0.5, 2)
    no_parse = True

    async def __call__(self, args, name, **void):
        if len(args) < 2:
            raise ArgumentError("일치시킬 두 개 이상의 문자열을 입력하십시오.")
        if name == "match":
            regex = None
            for i in (1, -1):
                s = args[i]
                if len(s) >= 2 and s[0] == s[1] == "/":
                    if regex:
                        raise ArgumentError("두 개의 정규식을 일치시킬 수 없습니다.")
                    regex = s[1:-1]
                    args.pop(i)
        else:
            regex = args.pop(0)
        if regex:
            temp = await create_future(re.findall, regex, " ".join(args))
            match = "\n".join(sqr_md(i) for i in temp)
        else:
            search = args.pop(0)
            s = " ".join(args)
            match = (
                sqr_md(round_min(round(fuzzy_substring(search, s) * 100, 6))) + "% literal match,\n"
                + sqr_md(round_min(round(fuzzy_substring(search.casefold(), s.casefold()) * 100, 6))) + "% case-insensitive match,\n"
                + sqr_md(round_min(round(fuzzy_substring(full_prune(search), full_prune(s)) * 100, 6))) + "% unicode mapping match."
            )
        return ini_md(match)


class Ask(Command):
    alias = ["How"]
    description = "어떤 질문이든 물어보세요, 제가 답변해드리겠습니다!"
    usage = "<문자열>"
    # flags = "h"
    no_parse = True
    rate_limit = (0.5, 1)
    slash = True

    convos = {}
    analysed = {}

    async def __call__(self, message, channel, user, argv, name, flags=(), **void):
        bot = self.bot
        guild = getattr(channel, "guild", None)
        count = bot.data.users.get(user.id, {}).get("last_talk", 0)
        add_dict(bot.data.users, {user.id: {"last_talk": 1, "last_mention": 1}})
        bot.data.users[user.id]["last_used"] = utc()
        bot.data.users.update(user.id)
        await bot.seen(user, event="misc", raw="Talking to me")

        if "dailies" in bot.data:
            bot.data.dailies.progress_quests(user, "talk")
        if name == "how":
            if not argv.replace("?", ""):
                q = name
            else:
                q = (name + " " + argv).lstrip()
        elif len(argv) > 1:
            q = unicode_prune(argv)
        else:
            q = argv
        q = q.replace("？", "?")
        if not q.replace("?", ""):
            return "\xad" + choice(
                "죄송합니다.못 봤습니다.질문이었나요? 🤔",
                "Ay, 말해봐, 난 물지 않아! :3",
                "하하, 좋은 시도입니다. 실제 질문이 아니라는 것을 알고 있습니다. 🙃",
                "실제 질문을 할 생각입니까?",
            )
        print(f"{message.author}:", q)
        if q.casefold() in ("how", "how?"):
            await send_with_reply(channel, message, "https://imgur.com/gallery/8cfRt")
            return
        # if AUTH.get("huggingface_token"):
        try:
            cb = self.convos[channel.id]
        except KeyError:
            if not convobot:
                cb = cdict(talk=lambda *args: "")
            else:
                cb = self.convos[channel.id] = convobot.Bot(token=AUTH["huggingface_token"])
        with discord.context_managers.Typing(channel):
            if getattr(message, "reference", None):
                reference = message.reference.resolved
                if TrOCRProcessor:
                    url = f"https://discord.com/channels/0/{channel.id}/{reference.id}"
                    found = await bot.follow_url(url)
                    if found and found[0] != url and is_image(found[0]) is not None:
                        url = found[0]
                        try:
                            prompt = self.analysed[url]
                        except KeyError:
                            processor = await create_future(TrOCRProcessor.from_pretrained, "nlpconnect/vit-gpt2-image-captioning")
                            model = await create_future(VisionEncoderDecoderModel.from_pretrained, "nlpconnect/vit-gpt2-image-captioning")
                            b = await bot.get_request(url)
                            with tracebacksuppressor:
                                image = Image.open(io.BytesIO(b)).convert("RGB")
                                pixel_values = processor(image, return_tensors="pt").pixel_values
                                generated_ids = await create_future(model.generate, pixel_values)
                                generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                                prompt = generated_text.strip()
                                if prompt:
                                    prompt = prompt.replace(" is ", ", ").replace(" are ", ", ")
                                    prompt = f"이것은 {prompt}이다"
                                    print(prompt)
                                    cb.append(prompt)
                                    spl = q.casefold().replace("'", " ").strip("?").split()
                                    if ("what" in spl or "who" in spl or "is" in spl or "name" in spl or "does") and ("this" in spl or "is" in spl or "that" in spl):
                                        cb.append(q)
                                        await send_with_reply(channel, message, "\xad" + escape_roles(prompt))
                                        self.analysed[url] = prompt
                                        return
                        else:
                            cb.append(prompt)
                if reference.content and not find_urls(reference.content):
                    print(reference.content)
                    cb.append(reference.content)
            if TrOCRProcessor:
                spl = q.casefold().replace("'", " ").strip("?").split()
                if find_urls(message.content) or message.attachments or message.embeds:
                    url = f"https://discord.com/channels/0/{channel.id}/{message.id}"
                    found = await bot.follow_url(url)
                    if found and found[0] != url and is_image(found[0]) is not None:
                        url = found[0]
                        try:
                            prompt = self.analysed[url]
                        except KeyError:
                            processor = await create_future(TrOCRProcessor.from_pretrained, "nlpconnect/vit-gpt2-image-captioning")
                            model = await create_future(VisionEncoderDecoderModel.from_pretrained, "nlpconnect/vit-gpt2-image-captioning")
                            b = await bot.get_request(url)
                            with tracebacksuppressor:
                                image = Image.open(io.BytesIO(b)).convert("RGB")
                                pixel_values = processor(image, return_tensors="pt").pixel_values
                                generated_ids = await create_future(model.generate, pixel_values)
                                generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                                prompt = generated_text.strip()
                                if prompt:
                                    prompt = prompt.replace(" is ", ", ").replace(" are ", ", ")
                                    prompt = f"이것은 {prompt}이다"
                                    print(prompt)
                                    cb.append(prompt)
                                    if ("what" in spl or "who" in spl or "is" in spl or "name" in spl or "does") and ("this" in spl or "is" in spl or "that" in spl):
                                        cb.append(q)
                                        await send_with_reply(channel, message, "\xad" + escape_roles(prompt))
                                        self.analysed[url] = prompt
                                        return
                        else:
                            cb.append(prompt)
            out = await create_future(cb.talk, q)
        if out:
            await send_with_reply(channel, message, lim_str("\xad" + escape_roles(out), 2000))
            return
        q = single_space(q).strip().translate(bot.mtrans).replace("?", "\u200b").strip("\u200b")
        out = None
        q = grammarly_2_point_0(q)
        if q == "why":
            out = "왜냐하면! :3"
        elif q == "what":
            out = "아무것도 아님! 🙃"
        elif q == "who":
            out = "누구, 나?"
        elif q == "when":
            out = "바로 지금!"
        elif q == "where":
            out = "여기,dummy"
        elif any(q.startswith(i) for i in ("what's ", "whats ", "what is ")) and regexp("[0-9]").search(q) and regexp("[+\\-*/\\\\^()").search(q):
            q = q[5:]
            q = q[q.index(" ") + 1:]
            try:
                if 0 <= q.rfind("<") < q.find(">"):
                    q = verify_id(q[q.rindex("<") + 1:q.index(">")])
                num = int(q)
            except ValueError:
                for _math in bot.commands.math:
                    answer = await _math(bot, q, "ask", channel, guild, {}, user)
                    if answer:
                        await send_with_reply(channel, "h" not in flags and message, answer)
                out = None
            else:
                if bot.in_cache(num) and "info" in bot.commands:
                    for _info in bot.commands.info:
                        await _info(num, None, "info", guild, channel, bot, user, "")
                    out = None
                else:
                    resp = await bot.solve_math(f"factorize {num}", timeout=20)
                    factors = safe_eval(resp[0])
                    out = f"{num}의 인수들은 `{', '.join(str(i) for i in factors)}`입니다. 더 많은 정보를 원하시면, {bot.get_prefix(guild)}수학을 시도하세요!"
        elif q.startswith("who's ") or q.startswith("whos ") or q.startswith("who is "):
            q = q[4:].split(None, 1)[-1]
            member = await bot.fetch_member_ex(q, guild, allow_banned=False, fuzzy=None)
            if member:
                if "info" in bot.commands:
                    for _info in bot.commands.info:
                        await _info(q, None, "info", guild, channel, bot, user, "")
                    out = None
            else:
                members = guild.members
                members.remove(bot.user)
                members.remove(user)
                target = choice(choice(members).name, choice(members).display_name)
                out = alist(
                    f"아마도 그것은 너의 {random.choice(['therapist', 'doctor', 'parent', 'sibling', 'friend'])}입니다!",
                    f"흠, 아마도 {target}!",
                    f"나는 그것이 {target}라고 확신합니다!",
                    f"내 생각에 {target}은 알고 있을 것입니다... 👀",
                    "나. 😏",
                )
                out = out[ihash(q) % len(out)]
        elif random.random() < 0.0625 + math.atan(count / 7) / 4:
            if xrand(3):
                if guild:
                    bots = [member for member in guild.members if member.bot and member.id != bot.id]
                answers = (
                    "해야할 일이 없습니까?",
                    "오류 : 시스템 백엔드가 연결을 거부했습니다. 나중에 다시 시도 해주십시오.",
                    "흥미롭군요. 잠시만 생각해보세요.",
                    "에이, 나 바쁘니까 나중에 물어봐!",
                    "¯\_(ツ)_/¯",
                    "흠, 모르겠어, 구글에 물어봤어?",
                    "죄송합니다. 인식하지 못했습니다. 다시 말씀해 주시겠습니까?",
                    "에이 나중에 물어봐 10시간짜리 튠즈하느라 바빠! 🎧",
                    "뭐라고?",
                    f"내 AI는 계속 성장하고 있어, 넌 뛰어야 할 것 같아. {get_random_emoji()}",
                    "답변할 질문이 필요한 경우 ~topic을 확인하십시오! 아, 그건 또 뭐였지?",
                )
                if bots:
                    answers += (f"🥱 피곤해...가서 물어봐 {user_mention(choice(bots).id)}...",)
                resp = choice(answers)
            else:
                response = (
                    "스스로에게 질문을 던질 때가 된 것 같아요!",
                    "내 대답에 대해 생각하는 동안 다음 질문이 있습니다:",
                    "당신을 위한 질문은 어떻습니까?",
                )
                resp = choice(response) + " " + choice(bot.data.users.questions)
            await send_with_reply(channel, message, resp)
            out = None
        elif any(q.startswith(i) for i in ("why ", "are ", "was ", "you ", "you're ")):
            out = alist(
                "모르겠는데 구글이 도움이 될까요?",
                f"너를 놀리기 위해, 나는 대답을 거부할게. {get_random_emoji()}",
                f"{choice('therapist', 'doctor', 'parent', 'sibling', 'friend')}에게 물어봐!",
                "왜 안돼",
                "그건 명백해,그렇죠? 😏",
                "머, 상관없나요?",
                "왜 그렇게 생각하세요?",
                "누가 알아?",
            )
            out = out[ihash(q) % len(out)]
        elif q.startswith("when "):
            dt = utc_dt()
            year = dt.year
            out = alist(
                f"올해 {random.randint(year, year + 10000)}!",
                f"In {sec2time(xrand(601) * 60)}!",
                f"난 그냥 봇이야, {user_mention(choice(bot.owners))} 는 아직 시간여행 코드를 찾지 못했습니다!",
                f"아마도 가서 {choice('일부 소셜 미니어 탐색', '유튜브 시청')}을 하고 그게 끝난 후에 확인해라!",
                "내일?",
                "백만년안에...",
                "지금 일어나기를 윈해? 가서 해봐!",
                "어제 그런거 아니야?",
                "절대. 😏",
                "한 시간 정도?",
                "그걸 시도하고 알아내!",
            )
            out = out[ihash(q) % len(out)]
        elif getattr((bot.commands.get(q.split(None, 1)[0]) or (None,))[0], "__name__", None) == "Hello":
            for _hello in bot.commands.hello:
                out = await _hello(bot, user, q.split(None, 1)[0], "".join(q.split(None, 1)[1:]), guild)
                if out:
                    await send_with_reply(channel, message, escape_roles(out))
                    return
        else:
            out = alist(
                "응!",
                "그래!",
                "으으음...네...?",
                "음! 😊",
                "나 그렇게 믿어?",
                "뭐? 아니!",
                "응!",
                "예 :3",
                "완전히!",
                "아마도?",
                "분명히!",
                "문론!",
                "그렇게 생각해요!",
                "나는 그렇게 생각?",
                "아마도?",
                "아마...",
                "아마 아니겠지?",
                "아닌 것 같아요",
                "아니 🙃",
                "정말 중요합니까?",
                "나도 몰라. ¯\_(ツ)_/¯",
                "그렇게 생각하지마...",
            )
            out = out[ihash(q) % len(out)]
        if out:
            q = q[0].upper() + q[1:]
            await send_with_reply(channel, message, escape_roles(f"\xad{q}? {out}"))


class Random(Command):
    name = ["choice", "choose", "랜덤선택"]
    description = "일련의 인수를 임의로 지정합니다."
    usage = "<문자열>+"
    slash = True

    def __call__(self, argv, args, **void):
        if not args:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        random.seed(time.time_ns())
        if "\n" in argv:
            x = choice(argv.splitlines())
        else:
            x = choice(args)
        return f"\xad나는 `{x}`을 선택합니다!"


class Rate(Command):
    name = ["Rating", "Rank", "Ranking", "평가"]
    description = "주어진 객체를 10점 만점의 임의의 값으로 평가합니다!"
    usage = "<문자열>"
    slash = True

    async def __call__(self, bot, guild, argv, **void):
        rate = random.randint(0, 10)
        pronoun = "that"
        lego = f"`{grammarly_2_point_1(argv)}`"
        try:
            user = await bot.fetch_member_ex(verify_id(argv), guild, allow_banned=False, fuzzy=None)
        except:
            if re.match("<a?:[A-Za-z0-9\\-~_]+:[0-9]+>", argv):
                lego = argv
                pronoun = "it"
        else:
            lego = f"`{user.display_name}`"
            rate = 10
            pronoun = "them"
        lego = lego.replace("?", "").replace("!", "")
        return f"{lego}? 나는 {pronoun}을 `{rate}/10`로 평가합니다!"

    
class WordCount(Command):
    name = ["Lc", "Wc", "Cc", "Character_Count", "Line_Count", "문자열수"]
    description = "제공된 메시지의 단어 및 문자 수를 반환하는 간단한 명령입니다. message.txt 파일도 작동합니다!"
    usage = "<문자열>"
    slash = True

    async def __call__(self, argv, **void):
        if not argv:
            raise ArgumentError("입력 문자열이 비어 있습니다.")
        if is_url(argv):
            argv = await self.bot.follow_url(argv, images=False)
        lc = argv.count("\n") + 1
        wc = len(argv.split())
        cc = len(argv)
        return f"줄 수: `{lc}`\n단어 수: `{wc}`\n문자 수: `{cc}`"


class Topic(Command):
    name = ["Question", "질문"]
    description = "임의의 질문을 던집니다."
    usage = "<관계{?r}>? <유혹하는말{?p}>? <nsfw유혹하는말{?n}>?"
    flags = "npr"
    
    def __call__(self, bot, user, flags, channel, **void):
        create_task(bot.seen(user, event="misc", raw="Talking to me"))
        if "r" in flags:
            return "\u200b" + choice(bot.data.users.rquestions)
        elif "p" in flags:
            return "\u200b" + choice(bot.data.users.pickup_lines)
        elif "n" in flags:
            if is_nsfw(channel):
                return "\u200b" + choice(bot.data.users.nsfw_pickup_lines)
            raise PermissionError(f"이 태그는 {uni_str('NSFW')}채널에서만 사용할 수 있습니다.")
        return "\u200b" + choice(bot.data.users.questions)


class Fact(Command):
    name = ["DailyFact", "UselessFact", "유용한사실"]
    description = "무작위 사실 제공."

    async def __call__(self, bot, user, **void):
        create_task(bot.seen(user, event="misc", raw="Talking to me"))
        fact = await bot.data.flavour.get(p=False, q=False)
        return "\u200b" + fact


class Urban(Command):
    time_consuming = True
    name = ["📖", "UrbanDictionary", "사전"]
    description = "항목에 대한 도시 사전 검색."
    usage = "<문자열>"
    flags = "v"
    rate_limit = (2, 8)
    typing = True
    slash = True
    header = {
        "accept-encoding": "application/gzip",
        "x-rapidapi-host": "mashape-community-urban-dictionary.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key,
    }

    async def __call__(self, channel, user, argv, message, **void):
        url = f"https://mashape-community-urban-dictionary.p.rapidapi.com/define?term={url_parse(argv)}"
        d = await Request(url, headers=self.header, timeout=12, json=True, aio=True)
        resp = d["list"]
        if not resp:
            raise LookupError(f"{argv}에 대한 결과 없음.")
        resp.sort(
            key=lambda e: scale_ratio(e.get("thumbs_up", 0), e.get("thumbs_down", 0)),
            reverse=True,
        )
        title = argv
        fields = deque()
        for e in resp:
            fields.append(dict(
                name=e.get("word", argv),
                value=ini_md(e.get("definition", "")),
                inline=False,
            ))
        self.bot.send_as_embeds(channel, title=title, fields=fields, author=get_author(user), reference=message)
