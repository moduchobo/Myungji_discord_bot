print = PRINT

import nekos, rule34, pybooru

# This entire module is a mess, I honestly don't care for it much
e_loop = asyncio.new_event_loop()
asyncio.set_event_loop(e_loop)
rule34_sync = rule34.Sync()
booruSites = list(pybooru.resources.SITE_LIST.keys())
LOG = False


def pull_e621(argv, delay=5):
    try:
        v1, v2 = 1, 1
        items = argv.replace(" ", "%20").casefold()
        baseurl = "https://e621.net/posts?tags="
        url = baseurl + items
        s = Request(url, decode=True)
        with suppress(ValueError):
            i = s.index("</a></li><li class='arrow'><a rel=\"next\"")
            sx = s[:i]
            ri = sx.rindex(">")
            pages = int(sx[ri + 1:])
            v1 = xrand(1, pages + 1)
            s = Request(f"{url}&page={v1}", decode=True)

        with suppress(ValueError):
            limit = s.index('class="next_page" rel="next"')
            s = s[:limit]

        search = ' data-file-url="'
        sources = deque()
        with suppress(ValueError):
            while True:
                ind1 = s.index(search)
                s = s[ind1 + len(search):]
                ind2 = s.index('"')
                target = s[:ind2]
                with suppress(ValueError):
                    sources.append(target)
        sources = list(sources)
        for _ in loop(8):
            v2 = xrand(len(sources))
            url = sources[v2]
            if is_image(url) is not None:
                break
        return [url, v1, v2 + 1]
    except:
        if LOG:
            print_exc()


def pull_booru(argv, delay=5):
    client = pybooru.Moebooru(choice(tuple(booruSites)))
    try:
        posts = client.post_list(tags=argv, random=True, limit=16)
        if not posts:
            raise EOFError
        i = xrand(len(posts))
        url = posts[i]["file_url"]
        return [url, 1, i + 1]
    except:
        if LOG:
            print_exc()


def pull_rule34_xxx(argv, delay=5):
    v1, v2 = 1, 1
    try:
        t = utc()
        while utc() - t < delay:
            with suppress(TimeoutError):
                sources = rule34_sync.getImages(
                    tags=argv,
                    fuzzy=True,
                    randomPID=True,
                    singlePage=True
                )
                break
        if sources:
            attempts = 0
            while attempts < 256:
                v2 = xrand(len(sources))
                url = sources[v2].file_url
                if is_image(url) is not None:
                    break
                attempts += 1
            if attempts >= 256:
                raise TimeoutError
            v1 = 1
            return [url, v1, v2 + 1]
        else:
            raise EOFError
    except:
        if LOG:
            print_exc()


def pull_rule34_paheal(argv, delay=5):
    try:
        v1, v2 = 1, 1
        items = argv.casefold().split(" ")
        if not len(argv.replace(" ", "")):
            tagsearch = [chr(i + 65) for i in range(26)]
        else:
            tagsearch = []
            for i in items:
                if i[0] not in tagsearch:
                    tagsearch.append(i[0])
        rx = xrand(len(tagsearch))
        baseurl = "https://rule34.paheal.net/tags/alphabetic?starts_with="
        url = baseurl + tagsearch[rx] + "&mincount=1"
        s = Request(url, decode=True)
        tags = s.split("href='/post/list/")[1:]
        valid = []
        for i in range(len(tags)):
            ind = tags[i].index("/")
            tags[i] = tags[i][:ind]
            t = tags[i].casefold()
            for a in items:
                if a in t or a[:-1] == t:
                    valid.append(tags[i])
        rx = xrand(len(valid))
        items = valid[rx]

        baseurl = "https://rule34.paheal.net/post/list/"
        try:
            s = Request(baseurl + items + "/1", decode=True)
        except ConnectionError:
            s = Request(baseurl + items.upper() + "/1", decode=True)
        with suppress(ValueError):
            ind = s.index('">Last</a><br>')
            s = s[ind - 5:ind]
            v1 = xrand(1, int(s.rsplit("/", 1)[-1]))
            url = url[:-1] + str(v1)

            s = Request(url, decode=True)
        with suppress(ValueError):
            limit = s.index("class=''>Images</h3><div class='blockbody'>")
            s = s[limit:]
            limit = s.index("</div></div></section>")
            s = s[:limit]

        search = 'href="'
        sources = []
        with suppress(ValueError):
            while True:
                ind1 = s.index(search)
                s = s[ind1 + len(search):]
                ind2 = s.index('"')
                target = s[:ind2]
                if not "." in target:
                    continue
                elif ".js" in target:
                    continue
                found = is_image(target) is not None
                if target[0] == "h" and found:
                    sources.append(target)
        v2 = xrand(len(sources))
        url = sources[v2]
        return [url, v1, v2 + 1]
    except:
        if LOG:
            print_exc()


async def searchRandomNSFW(argv, delay=10):
    funcs = [
        pull_booru,
        pull_rule34_paheal,
        pull_rule34_xxx,
        pull_e621,
    ]
    data = [create_future(f, argv, delay - 3) for f in funcs]
    out = deque()
    for fut in data:
        with tracebacksuppressor:
            temp = await fut
            if temp:
                out.append(temp)
    print(out)
    if not out:
        raise LookupError(f"{argv}에 대한 결과가 없습니다.")
    item = choice(out)
    return item


neko_tags = {
    "feet": True,
    "yuri": True,
    "trap": True,
    "futanari": True,
    "hololewd": True,
    "lewdkemo": True,
    "solog": True,
    "feetg": True,
    "cum": True,
    "erokemo": True,
    "les": True,
    "wallpaper": True,
    "lewdk": True,
    "ngif": True,
    "tickle": False,
    "lewd": True,
    "feed": False,
    "gecg": False,
    "eroyuri": True,
    "eron": True,
    "cum_jpg": True,
    "bj": True,
    "nsfw_neko_gif": True,
    "solo": True,
    "kemonomimi": True,
    "nsfw_avatar": True,
    "gasm": False,
    "poke": False,
    "anal": True,
    "slap": False,
    "hentai": True,
    "avatar": False,
    "erofeet": True,
    "holo": True,
    "keta": True,
    "blowjob": True,
    "pussy": True,
    "tits": True,
    "holoero": True,
    "lizard": False,
    "pussy_jpg": True,
    "pwankg": True,
    "classic": True,
    "kuni": True,
    "waifu": False,
    "pat": False,
    "8ball": False,
    "kiss": False,
    "femdom": True,
    "neko": False,
    "spank": True,
    "cuddle": False,
    "erok": True,
    "fox_girl": False,
    "boobs": True,
    "pussy": True,
    "random_hentai_gif": True,
    "hug": False,
    "ero": True,
    "smug": False,
    "goose": False,
    "baka": False,
    "cat": False,
    "dog": False,
    "gif": True,
    "meow": False,
    "woof": False,
    "404": False,
    "ass": True,
    "hmidriff": True,
    "hneko": True,
    "hkitsune": True,
    "kemonomimi": True,
    "kanna": False,
    "thigh": True,
    "gah": False,
    "coffee": False,
    "food": False,
    "paizuri": True,
    "tentacle": True,
    "yaoi": True,
}
nekobot_shared = {
    "hentai", "holo", "neko", "anal", "boobs"
}
nekobot_exclusive = {
    "ass", "hass", "hmidriff", "pgif", "4k", "hneko", "hkitsune", "kemonomimi", "hanal", "gonewild", "kanna",
    "thigh", "hthigh", "gah", "coffee", "food", "paizuri", "tentacle", "hboobs", "yaoi"
}


class Neko(Command):
    name = ["Nya", "고양이"]
    description = "nekos.life에서 임의의 이미지를 가져와서 삽입합니다."
    usage = "<태그(neko)>? <장황한{?v}|무작위{?r}|목록{?l}>?"
    flags = "lrv"
    rate_limit = (0, 4)
    threshold = 256
    moe_sem = Semaphore(1, 0, rate_limit=10)
    nekobot_sem = cdict()

    def img(self, tag=None):

        async def fetch(nekos, tag):
            if tag in (None, "neko"):
                tag = "neko"
                if not xrand(50) and not self.moe_sem.is_busy():
                    async with self.moe_sem:
                        resp = await Request(
                            "https://nekos.moe/api/v1/images/search",
                            data=orjson.dumps(dict(nsfw=False, limit=50, skip=xrand(10) * 50, sort="newest", artist="", uploader="")),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                            json=True,
                            aio=True,
                        )
                    out = set("https://nekos.moe/image/" + e["id"] for e in resp["images"])
                    if out:
                        print("nekos.moe", len(out))
                        return out
                if "neko" not in self.nekobot_sem:
                    self.nekobot_sem.neko = Semaphore(56, 56, rate_limit=61, last=True)
                if xrand(2) and not self.nekobot_sem.neko.is_busy():
                    nekobot_sem = self.nekobot_sem.neko
                    async with nekobot_sem:
                        data = await Request("https://nekobot.xyz/api/image?type=neko", aio=True, json=True)
                    return data["message"]
            if (tag in nekobot_exclusive or tag in nekobot_shared and xrand(2)):
                if tag not in self.nekobot_sem:
                    self.nekobot_sem[tag] = Semaphore(56, 56, rate_limit=61, last=True)
                nekobot_sem = self.nekobot_sem[tag]
                if tag in ("ass", "anal", "boobs", "thigh"):
                    tag = "h" + tag
                with suppress(SemaphoreOverflowError):
                    async with nekobot_sem:
                        url = f"https://nekobot.xyz/api/image?type={tag}"
                        # print(url, len(self.nekobot_sem.rate_bin))
                        data = await Request(url, aio=True, json=True)
                    return data["message"]
                return
            if tag == "meow":
                data = await Request("https://nekos.life/api/v2/img/meow", aio=True, json=True)
                return data["url"]
            return await create_future(nekos.img, tag)

        file = f"neko~{tag}" if tag else "neko"
        return self.bot.data.imagepools.get(file, fetch, self.threshold, args=(nekos, tag))

    async def __call__(self, bot, channel, flags, args, argv, **void):
        isNSFW = is_nsfw(channel)
        if "l" in flags or argv == "list":
            text = "**" + channel.name + "에서 사용 가능한 태그**:\n```ini\n"
            available = [k for k, v in neko_tags.items() if not v or isNSFW]
            text += str(sorted(available)) + "```"
            return text
        guild = getattr(channel, "guild", None)
        tagNSFW = False
        selected = []
        for tag in args:
            tag = tag.replace(",", "").casefold()
            if tag in neko_tags:
                if neko_tags.get(tag, 0) == True:
                    tagNSFW = True
                    if not isNSFW:
                        raise PermissionError(f"이 태그는{uni_str('NSFW')}채널에서만 사용할 수 있습니다.")
                selected.append(tag)
        if "r" in flags:
            if guild and guild.owner_id == bot.id and isNSFW and not xrand(100):
                selected = {}
            else:
                for _ in loop(flags["r"]):
                    possible = [k for k, v in neko_tags.items() if not v or isNSFW]
                    selected.append(choice(possible))
        if not selected:
            if isinstance(selected, dict):
                m = await bot.fetch_message(867429880596791327, bot.get_channel(849651458495610910))
                url = as_str(m.attachments[0].url)
            elif not argv:
                url = await self.img()
            else:
                raise LookupError(f"검색 태그 {argv}을 찾을 수 없습니다. 목록에서 {bot.get_prefix(guild)}neko 목록을 사용하세요.")
        else:
            v = xrand(len(selected))
            get = selected[v]
            if get == "gif":
                if tagNSFW and xrand(2):
                    url = await self.img("nsfw_neko_gif")
                else:
                    url = await self.img("ngif")
            elif get == "cat":
                url = await self.img("meow")
            elif get == "dog":
                url = await self.img("woof")
            elif get == "404":
                url = "https://cdn.nekos.life/smallboobs/404.png"
            else:
                url = await self.img(get)
        if "v" in flags:
            return escape_roles(url)
        embed = discord.Embed(colour=await bot.get_colour(url))
        embed.set_image(url=url)
        await send_with_react(channel, embed=embed, reacts="🔳")


class Lewd(Command):
    time_consuming = True
    _timeout_ = 2
    name = ["NSFW", "음란"]
    min_level = 1
    description = "Rule32 및 e621에 대한 검색에서 임의의 이미지를 가져와서 삽입합니다."
    usage = "<문의> <장황한{?v}>?"
    flags = "v"
    no_parse = True
    rate_limit = (1, 6)

    async def __call__(self, args, flags, message, channel, **void):
        if not is_nsfw(channel):
            raise PermissionError(f"이 명령은 {uni_str('NSFW')}채널에서만 사용할 수 있습니다.")
        objs = await searchRandomNSFW(" ".join(args), 12)
        url = verify_url(objs[0].strip().replace(" ", "%20"))
        if "v" in flags:
            text = (
                "Pulled from " + url
                + "\nImage **__" + str(objs[2])
                + "__** on page **__" + str(objs[1])
                + "__**"
            )
            return escape_roles(text)
        embed = discord.Embed(colour=await bot.get_colour(url))
        embed.set_image(url=url)
        await send_with_react(channel, embed=embed, reacts="🔳")