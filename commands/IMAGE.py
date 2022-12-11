print = PRINT

try:
    import yt_dlp as youtube_dl
except ModuleNotFoundError:
    import youtube_dl
import aiohttp

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
except ImportError:
    TrOCRProcessor = None
from PIL import Image
import imagebot

getattr(youtube_dl, "__builtins__", {})["print"] = print


ydl_opts = {
    "quiet": 1,
    "format": "bestvideo/best",
    "nocheckcertificate": 1,
    "no_call_home": 1,
    "nooverwrites": 1,
    "noplaylist": 1,
    "logtostderr": 0,
    "ignoreerrors": 0,
    "default_search": "auto",
    "source_address": "0.0.0.0",
}
downloader = youtube_dl.YoutubeDL(ydl_opts)

def get_video(url, fps=None):
    try:
        entry = downloader.extract_info(url, download=False)
    except:
        print_exc()
        return url, None, None, None
    best = 0
    size = None
    dur = None
    try:
        fmts = entry["formats"]
    except KeyError:
        fmts = ""
    for fmt in fmts:
        q = fmt.get("height", 0)
        if type(q) is not int:
            q = 0
        # Attempt to get as close to 720p as possible for download
        if abs(q - 720) < abs(best - 720):
            best = q
            url = fmt["url"]
            size = [fmt["width"], fmt["height"]]
            dur = fmt.get("duration", entry.get("duration"))
            fps = fmt.get("fps", entry.get("fps"))
    if "dropbox.com" in url:
        if "?dl=0" in url:
            url = url.replace("?dl=0", "?dl=1")
    return url, size, dur, fps

VIDEOS = ("gif", "webp", "apng", "mp4", "mkv", "webm", "mov", "wmv", "flv", "avi", "qt", "f4v", "zip")


class IMG(Command):
    min_display = "0~2"
    name=["이미지"]
    description ="리스트에 있는 이미지를 현재 채팅에 전송한다."
    usage = "(추가|삭제)? <0:태그>* <1:이미지url>? <verbose{?v}|delete{?x}|hide{?h}>?"
    flags = "vraedhzfx"
    no_parse = True
    directions = [b'\xe2\x8f\xab', b'\xf0\x9f\x94\xbc', b'\xf0\x9f\x94\xbd', b'\xe2\x8f\xac', b'\xf0\x9f\x94\x84']
    dirnames = ["First", "Prev", "Next", "Last", "Refresh"]
    slash = True

    async def __call__(self, bot, flags, args, argv, user, message, channel, guild, perm, **void):
        update = bot.data.images.update
        imglists = bot.data.images
        images = imglists.get(guild.id, {})
        if "a" in flags or "e" in flags or "d" in flags:
            if message.attachments:
                args.extend(best_url(a) for a in message.attachments)
                argv += " " * bool(argv) + " ".join(best_url(a) for a in message.attachments)
            req = 2
            if perm < req:
                reason = "to change image list for " + guild.name
                raise self.perm_error(perm, req, reason)
            if "a" in flags or "e" in flags:
                lim = 256 << bot.is_trusted(guild.id) * 2 + 1
                if len(images) > lim:
                    raise OverflowError(f"Image list for {guild} has reached the maximum of {lim} items. Please remove an item to add another.")
                key = " ".join(args[:-1]).casefold()
                if len(key) > 2000:
                    raise ArgumentError("Image tag too long.")
                elif not key:
                    raise ArgumentError("Image tag must not be empty.")
                if is_url(args[0]):
                    if len(args) > 1:
                        args = (args[-1], args[0])
                    else:
                        args = (args[0].split("?", 1)[0].rsplit("/", 1)[-1].rsplit(".", 1)[0], args[0])
                urls = await bot.follow_url(args[-1], best=True, allow=True, limit=1)
                url = urls[0]
                if len(url) > 2000:
                    raise ArgumentError("Image url too long.")
                images[key] = url
                images = {i: images[i] for i in sorted(images)}
                imglists[guild.id] = images
                if not "h" in flags:
                    return css_md(f"Successfully added {sqr_md(key)} to the image list for {sqr_md(guild)}.")
            if not args:
                # This deletes all images for the current guild
                if "f" not in flags and len(images) > 1:
                    return css_md(sqr_md(f"WARNING: {len(images)} IMAGES TARGETED. REPEAT COMMAND WITH ?F FLAG TO CONFIRM."), force=True)
                imglists[guild.id] = {}
                return italics(css_md(f"Successfully removed all {sqr_md(len(images))} images from the image list for {sqr_md(guild)}."))
            key = argv.casefold()
            images.pop(key)
            imglists[guild.id] = images
            return italics(css_md(f"Successfully removed {sqr_md(key)} from the image list for {sqr_md(guild)}."))
        if not argv and not "r" in flags:
            # Set callback message for scrollable list
            buttons = [cdict(emoji=dirn, name=name, custom_id=dirn) for dirn, name in zip(map(as_str, self.directions), self.dirnames)]
            await send_with_reply(
                None,
                message,
                "*```" + "\n" * ("z" in flags) + "callback-image-img-"
                + str(user.id) + "_0"
                + "-\nLoading Image database...```*",
                buttons=buttons
            )
            return
        sources = alist()
        for tag in args:
            t = tag.casefold()
            if t in images:
                sources.append(images[t])
        r = flags.get("r", 0)
        for _ in loop(r):
            sources.append(choice(images.values()))
        if not len(sources):
            raise LookupError(f"Target image {argv} not found. Use img for list.")
        url = choice(sources)
        if "x" in flags:
            create_task(bot.silent_delete(message))
        if "v" in flags:
            msg = escape_roles(url)
        else:
            msg = None
        url2 = await bot.get_proxy_url(message.author)
        colour = await create_future(bot.get_colour, message.author)
        emb = discord.Embed(colour=colour, url=url).set_image(url=url)
        await bot.send_as_webhook(channel, msg, embed=emb, username=message.author.display_name, avatar_url=url2)

    async def _callback_(self, bot, message, reaction, user, perm, vals, **void):
        u_id, pos = list(map(int, vals.split("_", 1)))
        if reaction not in (None, self.directions[-1]) and u_id != user.id and perm < 3:
            return
        if reaction not in self.directions and reaction is not None:
            return
        guild = message.guild
        user = await bot.fetch_user(u_id)
        imglists = bot.data.images
        images = imglists.get(guild.id, {})
        page = 12
        last = max(0, len(images) - page)
        if reaction is not None:
            i = self.directions.index(reaction)
            if i == 0:
                new = 0
            elif i == 1:
                new = max(0, pos - page)
            elif i == 2:
                new = min(last, pos + page)
            elif i == 3:
                new = last
            else:
                new = pos
            pos = new
        content = message.content
        if not content:
            content = message.embeds[0].description
        i = content.index("callback")
        content = "*```" + "\n" * ("\n" in content[:i]) + (
            "callback-image-img-"
            + str(u_id) + "_" + str(pos)
            + "-\n"
        )
        if not images:
            content += f"Image list for {str(guild).replace('`', '')} is currently empty.```*"
            msg = ""
        else:
            content += f"{len(images)} images currently assigned for {str(guild).replace('`', '')}:```*"
            msg = ini_md(iter2str({k: "\n" + images[k] for k in tuple(images)[pos:pos + page]}))
        colour = await self.bot.get_colour(guild)
        emb = discord.Embed(
            description=content + msg,
            colour=colour,
        )
        emb.set_author(**get_author(user))
        more = len(images) - pos - page
        if more > 0:
            emb.set_footer(text=f"{uni_str('And', 1)} {more} {uni_str('more...', 1)}")
        create_task(message.edit(content=None, embed=emb, allowed_mentions=discord.AllowedMentions.none()))
        if hasattr(message, "int_token"):
            await bot.ignore_interaction(message)


async def get_image(bot, user, message, args, argv, default=2, raw=False, ext="png"):
    try:
        # Take input from any attachments, or otherwise the message contents
        if message.attachments:
            args = [best_url(a) for a in message.attachments] + args
            argv = " ".join(best_url(a) for a in message.attachments) + " " * bool(argv) + argv
        if not args:
            raise ArgumentError
        url = args.pop(0)
        urls = await bot.follow_url(url, best=True, allow=True, limit=1)
        if not urls:
            urls = await bot.follow_to_image(argv)
            if not urls:
                urls = await bot.follow_to_image(url)
                if not urls:
                    raise ArgumentError
        url = urls[0]
    except ArgumentError:
        if not argv:
            url = None
            try:
                url = await bot.get_last_image(message.channel)
            except FileNotFoundError:
                raise ArgumentError("Please input an image by URL or attachment.")
        else:
            raise ArgumentError("Please input an image by URL or attachment.")
    if args and args[-1] in VIDEOS:
        ext = args.pop(-1)
    value = " ".join(args).strip()
    if not value:
        value = default
    elif not raw:
        value = await bot.eval_math(value)
        if not abs(value) <= 256:
            raise OverflowError("Maximum multiplier input is 256.")
    # Try and find a good name for the output image
    try:
        name = url[url.rindex("/") + 1:]
        if not name:
            raise ValueError
        if "." in name:
            name = name[:name.rindex(".")]
    except ValueError:
        name = "unknown"
    if not name.endswith("." + ext):
        name += "." + ext
    return name, value, url, ext


class ImageAdjust(Command):
    name = [
        "Saturation", "Saturate",
        "Contrast",
        "Brightness", "Brighten", "Lighten", "Lightness",
        "Luminance", "Luminosity",
        "Sharpness", "Sharpen",
        "HueShift", "Hue",
        "Blur", "Gaussian", "이미지조정"
    ]
    description = "Applies an adjustment filter to the supplied image. 제공된 이미지에 조정 필터를 적용한다"
    usage = "<0:이미지url> <1:multiplier(2)>?"
    no_parse = True
    rate_limit = (2, 5)
    _timeout_ = 3
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, name, _timeout, **void):
        if name.startswith("hue"):
            default = 0.5
        elif name in ("blur", "gaussian"):
            default = 8
        else:
            default = 2
        name2, value, url, fmt = await get_image(bot, user, message, args, argv, default=default)
        with discord.context_managers.Typing(channel):
            if name.startswith("sat"):
                argi = ("Enhance", ["Color", value, "-f", fmt])
            elif name.startswith("con"):
                argi = ("Enhance", ["Contrast", value, "-f", fmt])
            elif name.startswith("bri") or name.startswith("lig"):
                argi = ("brightness", [value, "-f", fmt])
            elif name.startswith("lum"):
                argi = ("luminance", [value, "-f", fmt])
            elif name.startswith("sha"):
                argi = ("Enhance", ["Sharpness", value, "-f", fmt])
            elif name.startswith("hue"):
                argi = ("hue_shift", [value, "-f", fmt])
            elif name in ("blur", "gaussian"):
                argi = ("blur", ["gaussian", value, "-f", fmt])
            else:
                raise RuntimeError(name)
            resp = await process_image(url, *argi, timeout=_timeout)
            fn = resp[0]
            if fn.endswith(".gif"):
                if not name2.endswith(".gif"):
                    if "." in name2:
                        name2 = name2[:name2.rindex(".")]
                    name2 += ".gif"
        await bot.send_with_file(channel, "", fn, filename=name2, reference=message)


class ColourDeficiency(Command):
    name = ["ColorBlind", "ColourBlind", "ColorBlindness", "ColourBlindness", "ColorDeficiency","색맹필터적용"]
    alias = name + ["Protanopia", "Protanomaly", "Deuteranopia", "Deuteranomaly", "Tritanopia", "Tritanomaly", "Achromatopsia", "Achromatonomaly"]
    description = "대상 이미지에 색맹 필터를 적용한다"
    usage = "<0:이미지url> (protanopia|protanomaly|deuteranopia|deuteranomaly|tritanopia|tritanomaly|achromatopsia|achromatonomaly)? <1:비율(0.9)>?"
    no_parse = True
    rate_limit = (3, 7)
    _timeout_ = 3.5
    typing = True

    async def __call__(self, bot, user, channel, message, name, args, argv, _timeout, **void):
        # Take input from any attachments, or otherwise the message contents
        if message.attachments:
            args = [best_url(a) for a in message.attachments] + args
            argv = " ".join(best_url(a) for a in message.attachments) + " " * bool(argv) + argv
        try:
            if not args:
                raise ArgumentError
            url = args.pop(0)
            urls = await bot.follow_url(url, best=True, allow=True, limit=1)
            if not urls:
                urls = await bot.follow_to_image(argv)
                if not urls:
                    urls = await bot.follow_to_image(url)
                    if not urls:
                        raise ArgumentError
            url = urls[0]
        except ArgumentError:
            if not argv:
                url = None
                try:
                    url = await bot.get_last_image(message.channel)
                except FileNotFoundError:
                    raise ArgumentError("Please input an image by URL or attachment.")
            else:
                raise ArgumentError("Please input an image by URL or attachment.")
        if "color" not in name and "colour" not in name:
            operation = name
        elif args:
            operation = args.pop(0).casefold()
        else:
            operation = "deuteranomaly"
        value = " ".join(args).strip()
        if not value:
            value = None
        else:
            value = await bot.eval_math(value)
            if not abs(value) <= 2:
                raise OverflowError("Maximum multiplier input is 2.")
        # Try and find a good name for the output image
        try:
            name = url[url.rindex("/") + 1:]
            if not name:
                raise ValueError
            if "." in name:
                name = name[:name.rindex(".")]
        except ValueError:
            name = "unknown"
        ext = "png"
        if not name.endswith("." + ext):
            name += "." + ext
        with discord.context_managers.Typing(channel):
            resp = await process_image(url, "colour_deficiency", [operation, value], timeout=_timeout)
            fn = resp[0]
            if fn.endswith(".gif"):
                if not name.endswith(".gif"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".gif"
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


# class RemoveMatte(Command):
#     name = ["RemoveColor", "RemoveColour"]
#     description = "Removes a colour from the supplied image."
#     usage = "<0:url> <colour(#FFFFFF)>?"
#     no_parse = True
#     rate_limit = (4, 9)
#     _timeout_ = 4.5
#     typing = True

#     async def __call__(self, bot, user, channel, message, name, args, argv, _timeout, **void):
#         # Take input from any attachments, or otherwise the message contents
#         if message.attachments:
#             args = [best_url(a) for a in message.attachments] + args
#             argv = " ".join(best_url(a) for a in message.attachments) + " " * bool(argv) + argv
#         try:
#             if not args:
#                 raise ArgumentError
#             url = args.pop(0)
#             urls = await bot.follow_url(url, best=True, allow=True, limit=1)
#             if not urls:
#                 urls = await bot.follow_to_image(argv)
#                 if not urls:
#                     urls = await bot.follow_to_image(url)
#                     if not urls:
#                         raise ArgumentError
#             url = urls[0]
#         except ArgumentError:
#             if not argv:
#                 url = None
#                 try:
#                     url = await bot.get_last_image(message.channel)
#                 except FileNotFoundError:
#                     raise ArgumentError("Please input an image by URL or attachment.")
#             else:
#                 raise ArgumentError("Please input an image by URL or attachment.")
#         colour = parse_colour(" ".join(args), default=(255,) * 3)
#         # Try and find a good name for the output image
#         try:
#             name = url[url.rindex("/") + 1:]
#             if not name:
#                 raise ValueError
#             if "." in name:
#                 name = name[:name.rindex(".")]
#         except ValueError:
#             name = "unknown"
#         ext = "png"
#         if not name.endswith("." + ext):
#             name += "." + ext
#         with discord.context_managers.Typing(channel):
#             resp = await process_image(url, "remove_matte", [colour], timeout=_timeout)
#             fn = resp[0]
#             if fn.endswith(".gif"):
#                 if not name.endswith(".gif"):
#                     if "." in name:
#                         name = name[:name.rindex(".")]
#                     name += ".gif"
#         await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Invert(Command):
    name = ["Negate","반전","인버트"]
    description = "제공된 이미지를 반전한다."
    usage = "<이미지url>"
    no_parse = True
    rate_limit = (2, 4.5)
    _timeout_ = 3
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, _timeout, **void):
        name, value, url, fmt = await get_image(bot, user, message, args, argv)
        with discord.context_managers.Typing(channel):
            resp = await process_image(url, "invert", ["-f", fmt], timeout=_timeout)
            fn = resp[0]
            if fn.endswith(".gif"):
                if not name.endswith(".gif"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".gif"
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class GreyScale(Command):
    name = ["GrayScale","그레이스케일","그레이","회색"]
    description = "제공된 이미지의 회색 스케일을 제공"
    usage = "<이미지url>"
    no_parse = True
    rate_limit = (2, 4.5)
    _timeout_ = 3
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, _timeout, **void):
        name, value, url, fmt = await get_image(bot, user, message, args, argv)
        with discord.context_managers.Typing(channel):
            resp = await process_image(url, "greyscale", ["-f", fmt], timeout=_timeout)
            fn = resp[0]
            if fn.endswith(".gif"):
                if not name.endswith(".gif"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".gif"
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Laplacian(Command):
    name = ["EdgeDetect", "Edges","모서리","라플라시안"]
    description = "라플라시안 모서리 감지 알고리즘을 이미지에 적용한다."
    usage = "<이미지url>"
    no_parse = True
    rate_limit = (2, 4.5)
    _timeout_ = 3
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, _timeout, **void):
        name, value, url, fmt = await get_image(bot, user, message, args, argv)
        with discord.context_managers.Typing(channel):
            resp = await process_image(url, "laplacian", ["-f", fmt], timeout=_timeout)
            fn = resp[0]
            if fn.endswith(".gif"):
                if not name.endswith(".gif"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".gif"
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class ColourSpace(Command):
    name = ["ColorSpace","색공간","컬러스페이스"]
    description = "제공된 이미지의 색 공간을 변경한다."
    usage = "<0:이미지url> <2:색상(rgb)>? <1:dest(hsv)>?"
    no_parse = True
    rate_limit = (3, 6.5)
    _timeout_ = 4
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, _timeout, **void):
        name, value, url, fmt = await get_image(bot, user, message, args, argv, raw=True, default="")
        spl = value.rsplit(None, 1)
        if not spl:
            source = "rgb"
            dest = "hsv"
        elif len(spl) == 1:
            source = "rgb"
            dest = spl[0].casefold()
        else:
            source, dest = (i.casefold() for i in spl)
        if source == dest:
            raise TypeError("Colour spaces must be different.")
        for i in (source, dest):
            if i not in ("rgb", "cmy", "xyz", "hsv", "hsl", "hsi", "hcl", "lab", "luv", "yiq", "yuv"):
                raise TypeError(f"Invalid colour space {i}.")
        with discord.context_managers.Typing(channel):
            resp = await process_image(url, "colourspace", [source, dest, "-f", fmt], timeout=_timeout)
            fn = resp[0]
            if fn.endswith(".gif"):
                if not name.endswith(".gif"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".gif"
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Magik(Command):
    name = ["Distort","매직","매직필터"]
    description = "이미지에 Magik 이미지 필터를 적용한다."
    usage = "<0:이미지url> <cell_count(7)>?"
    no_parse = True
    rate_limit = (3, 7)
    _timeout_ = 4
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, _timeout, **void):
        name, value, url, fmt = await get_image(bot, user, message, args, argv, default=7)
        with discord.context_managers.Typing(channel):
            resp = await process_image(url, "magik", [value, "-f", fmt], timeout=_timeout)
            fn = resp[0]
            if fn.endswith(".gif"):
                if not name.endswith(".gif"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".gif"
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Colour(Command):
    name = ["RGB", "HSV", "HSL", "CMY", "LAB", "LUV", "XYZ", "Color","색깔","컬러"]
    description = "입력한 컬러의 128x128사이즈의 이미지를 생성한다."
    usage = "<색상>"
    no_parse = True
    rate_limit = (1, 3)
    flags = "v"
    trans = {
        "hsv": hsv_to_rgb,
        "hsl": hsl_to_rgb,
        "cmy": cmy_to_rgb,
        "lab": lab_to_rgb,
        "luv": luv_to_rgb,
        "xyz": xyz_to_rgb,
    }
    typing = True
    slash = True

    async def __call__(self, bot, user, message, channel, name, argv, **void):
        channels = parse_colour(argv)
        if name in self.trans:
            if name in "lab luv":
                adj = channels
            else:
                adj = [x / 255 for x in channels]
            channels = [round(x * 255) for x in self.trans[name](adj)]
        adj = [x / 255 for x in channels]
        # Any exceptions encountered during colour transformations will immediately terminate the command
        msg = ini_md(
            "HEX colour code: " + sqr_md(bytes(channels).hex().upper())
            + "\nDEC colour code: " + sqr_md(colour2raw(channels))
            + "\nRGB values: " + str(channels if type(channels) is list else list(channels))
            + "\nHSV values: " + sqr_md(", ".join(str(round(x * 255)) for x in rgb_to_hsv(adj)))
            + "\nHSL values: " + sqr_md(", ".join(str(round(x * 255)) for x in rgb_to_hsl(adj)))
            + "\nCMY values: " + sqr_md(", ".join(str(round(x * 255)) for x in rgb_to_cmy(adj)))
            + "\nLAB values: " + sqr_md(", ".join(str(round(x)) for x in rgb_to_lab(adj)))
            + "\nLUV values: " + sqr_md(", ".join(str(round(x)) for x in rgb_to_luv(adj)))
            + "\nXYZ values: " + sqr_md(", ".join(str(round(x * 255)) for x in rgb_to_xyz(adj)))
        )
        with discord.context_managers.Typing(channel):
            resp = await process_image("from_colour", "$", [channels])
            fn = resp[0]
            f = CompatFile(fn, filename="colour.png")
        await bot.send_with_file(channel, msg, f, filename=fn, best=True, reference=message)


class Gradient(Command):
    name=["그라데이션"]
    description = "특정 모양의 그라데이션을 생성한다." 
    usage = "(linear|radial|conical|spiral|polygon)? <0:count(1)>? <1:색상(white)>?"
    no_parse = True
    rate_limit = (2, 5)
    typing = True

    async def __call__(self, bot, user, message, channel, args, **void):
        if not args:
            shape = "linear"
        else:
            shape = args.pop(0)
        if shape not in "linear|radial|conical|spiral|polygon".split("|"):
            raise TypeError(f"Invalid gradient shape {args[0]}.")
        if args:
            colour = args.pop(-1)
            colour = parse_colour(colour)
        else:
            colour = (255,) * 3
        if args:
            count = await bot.eval_math(" ".join(args))
        else:
            count = 1
        with discord.context_managers.Typing(channel):
            resp = await process_image("from_gradient", "$", [shape, count, colour])
            fn = resp[0]
            f = CompatFile(fn, filename="gradient.png")
        await bot.send_with_file(channel, "", f, filename=fn, best=True, reference=message)


class Average(Command):
    name = ["AverageColour","평균","평균색상"]
    description = "이미지의 평균 픽셀 색상(RGB)을 계산한다."
    usage = "<이미지url>"
    no_parse = True
    rate_limit = (2, 6)
    _timeout_ = 2
    typing = True

    async def __call__(self, bot, channel, user, message, argv, args, **void):
        if message.attachments:
            args = [worst_url(a) for a in message.attachments] + args
            argv = " ".join(worst_url(a) for a in message.attachments) + " " * bool(argv) + argv
        try:
            if not args:
                raise ArgumentError
            url = args.pop(0)
            urls = await bot.follow_url(url, best=True, allow=True, limit=1)
            if not urls:
                urls = await bot.follow_to_image(argv)
                if not urls:
                    urls = await bot.follow_to_image(url)
                    if not urls:
                        raise ArgumentError
            url = urls[0]
        except ArgumentError:
            if not argv:
                url = None
                try:
                    url = await bot.get_last_image(message.channel)
                except FileNotFoundError:
                    raise ArgumentError("Please input an image by URL or attachment.")
            else:
                raise ArgumentError("Please input an image by URL or attachment.")
        with discord.context_managers.Typing(channel):
            colour = await bot.data.colours.get(url, threshold=False)
            channels = raw2colour(colour)
            adj = [x / 255 for x in channels]
            # Any exceptions encountered during colour transformations will immediately terminate the command
            msg = ini_md(
                "HEX colour code: " + sqr_md(bytes(channels).hex().upper())
                + "\nDEC colour code: " + sqr_md(colour2raw(channels))
                + "\nRGB values: " + str(channels)
                + "\nHSV values: " + sqr_md(", ".join(str(round(x * 255)) for x in rgb_to_hsv(adj)))
                + "\nHSL values: " + sqr_md(", ".join(str(round(x * 255)) for x in rgb_to_hsl(adj)))
                + "\nCMY values: " + sqr_md(", ".join(str(round(x * 255)) for x in rgb_to_cmy(adj)))
                + "\nLAB values: " + sqr_md(", ".join(str(round(x)) for x in rgb_to_lab(adj)))
                + "\nLUV values: " + sqr_md(", ".join(str(round(x)) for x in rgb_to_luv(adj)))
                + "\nXYZ values: " + sqr_md(", ".join(str(round(x * 255)) for x in rgb_to_xyz(adj)))
            )
            resp = await process_image("from_colour", "$", [channels])
            fn = resp[0]
            f = CompatFile(fn, filename="average.png")
        await bot.send_with_file(channel, msg, f, filename=fn, best=True, reference=message)
        # return css_md("#" + bytes2hex(bytes(raw2colour(colour)), space=False))


class QR(Command):
    name = ["RainbowQR","큐알코드","큐알"]
    description = "입력 문자열에서 QR 코드 이미지를 생성하고 선택적으로 레인보우 스월 효과를 추가합니다."
    usage = "<문자열>"
    no_parse = True
    rate_limit = (3, 7)
    _timeout_ = 4
    typing = True

    async def __call__(self, bot, message, channel, argv, name, _timeout, **void):
        if not argv:
            raise ArgumentError("Input string is empty.")
        with discord.context_managers.Typing(channel):
            resp = await process_image("to_qr", "$", [argv, "rainbow" in name], timeout=_timeout)
            fn = resp[0]
        await bot.send_with_file(channel, "", fn, filename="QR." + ("gif" if "rainbow" in name else "png"), reference=message)


class Rainbow(Command):
    name = ["RainbowGIF", "Gay","레인보우"]
    description = "제공된 이미지를 반복적으로 색조 이동하여 .gif 이미지를 만듭니다."
    usage = "<0:이미지url> <1:duration(2)>?"
    no_parse = True
    rate_limit = (5, 12)
    _timeout_ = 8
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, _timeout, **void):
        name, value, url, fmt = await get_image(bot, user, message, args, argv, ext="gif")
        with discord.context_managers.Typing(channel):
            # -gif signals to image subprocess that the output is always a .gif image
            resp = await process_image(url, "rainbow_gif", [value, "-gif", "-f", fmt], timeout=_timeout)
            fn = resp[0]
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Scroll(Command):
    name = ["Parallax", "Offset", "ScrollGIF","스크롤"]
    description = "제공된 이미지를 지정된 방향으로 반복적으로 이동하여 .gif 이미지를 만듭니다."
    usage = "<0:이미지url> <1:방향(left)>? <2:duration(2)>? <3:fps(32)>?"
    no_parse = True
    rate_limit = (5, 11)
    _timeout_ = 8
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, _timeout, **void):
        try:
            if message.attachments:
                args = [best_url(a) for a in message.attachments] + args
                argv = " ".join(best_url(a) for a in message.attachments) + " " * bool(argv) + argv
            if not args:
                raise ArgumentError
            url = args.pop(0)
            urls = await bot.follow_url(url, best=True, allow=True, limit=1)
            if not urls:
                urls = await bot.follow_to_image(argv)
                if not urls:
                    urls = await bot.follow_to_image(url)
                    if not urls:
                        raise ArgumentError
            url = urls[0]
        except ArgumentError:
            if not argv:
                url = None
                try:
                    url = await bot.get_last_image(message.channel)
                except FileNotFoundError:
                    raise ArgumentError("Please input an image by URL or attachment.")
            else:
                raise ArgumentError("Please input an image by URL or attachment.")
        if args:
            direction = args.pop(0)
        else:
            direction = "LEFT"
        if args:
            duration = await bot.eval_math(args.pop(0))
        else:
            duration = 2
        if args:
            fps = await bot.eval_math(" ".join(args))
            fps = round(fps)
            if fps <= 0:
                raise ValueError("FPS value must be positive.")
            elif fps > 64:
                raise OverflowError("Maximum FPS value is 64.")
        else:
            fps = 32
        try:
            name = url[url.rindex("/") + 1:]
            if not name:
                raise ValueError
            if "." in name:
                name = name[:name.rindex(".")]
        except ValueError:
            name = "unknown"
        if not name.endswith(".gif"):
            name += ".gif"
        with discord.context_managers.Typing(channel):
            # -gif signals to image subprocess that the output is always a .gif image
            resp = await process_image(url, "scroll_gif", [direction, duration, fps, "-gif"], timeout=_timeout)
            fn = resp[0]
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Spin(Command):
    name = ["SpinGIF","스핀"]
    description = "이미지를 반복적으로 회전하여 .gif 이미지를 만듭니다."
    usage = "<0:이미지url> <1:duration(2)>?"
    no_parse = True
    rate_limit = (5, 11)
    _timeout_ = 8
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, _timeout, **void):
        name, value, url, fmt = await get_image(bot, user, message, args, argv, ext="gif")
        with discord.context_managers.Typing(channel):
            # -gif signals to image subprocess that the output is always a .gif image
            resp = await process_image(url, "spin_gif", [value, "-gif", "-f", fmt], timeout=_timeout)
            fn = resp[0]
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Orbit(Command):
    name = ["Orbital", "Orbitals","오르빗","궤도"]
    description = "이미지의 궤도 스프라이트 링을 렌더링합니다."
    usage = "<0:이미지url> <1:orbital_count(5)>? <2:duration(2)>?"
    no_parse = True
    rate_limit = (8, 19)
    _timeout_ = 13
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, _timeout, **void):
        name, value, url, fmt = await get_image(bot, user, message, args, argv, ext="gif", raw=True, default="")
        extras = deque()
        while value:
            spl = value.split(None, 1)
            urls = await bot.follow_url(spl[0], best=True, allow=True, limit=1)
            if not urls:
                break
            value = spl[-1] if len(spl) > 1 else ""
            extras.append(urls[0])
        # if extras:
        #     print(url, *extras)
        spl = value.rsplit(None, 1)
        if not spl:
            if not extras:
                count = 5
            else:
                count = len(extras) + 1
            duration = 2
        elif len(spl) == 1:
            if not extras:
                count = await bot.eval_math(spl[0])
                duration = 2
            else:
                count = len(extras) + 1
                duration = await bot.eval_math(spl[0])
        else:
            count = await bot.eval_math(spl[0])
            duration = await bot.eval_math(spl[1])
        if count > 64:
            raise OverflowError()
        with discord.context_managers.Typing(channel):
            resp = await process_image(url, "orbit_gif", [count, duration, list(extras), "-gif", "-f", fmt], timeout=_timeout)
            fn = resp[0]
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class GMagik(Command):
    name = ["Liquefy", "MagikGIF","반복매직","G매직"]
    description = "이미지에 Magik 이미지 필터를 반복적으로 적용합니다."
    usage = "<0:이미지url> <cell_size(7)>?"
    no_parse = True
    rate_limit = (7, 13)
    _timeout_ = 8
    typing = True

    async def __call__(self, bot, user, channel, message, name, args, argv, _timeout, **void):
        if name == "liquefy":
            default = 32
        else:
            default = 7
        name, value, url, fmt = await get_image(bot, user, message, args, argv, default=default, ext="gif")
        if name == "liquefy":
            arr = [abs(value), 2, "-gif", "-f", fmt]
        else:
            arr = [abs(value), "-gif", "-f", fmt]
        with discord.context_managers.Typing(channel):
            resp = await process_image(url, "magik_gif", arr, timeout=_timeout)
            fn = resp[0]
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class CreateGIF(Command):
    name = ["Animate", "GIF", "Frames", "ImageSequence","gif생성"]
    description = "제공된 여러 이미지 및/또는 선택적으로 비디오를 애니메이션 이미지, 이미지 시퀀스 또는 비디오로 결합합니다."
    usage = "<0:이미지url>+ <-2:fps(20)>? <-1:파일 형식(gif)>?"
    no_parse = True
    rate_limit = (8, 24)
    _timeout_ = 20
    flags = "r"
    typing = True

    async def __call__(self, bot, user, guild, channel, message, flags, name, args, _timeout, **void):
        # Take input from any attachments, or otherwise the message contents
        if message.attachments:
            args += [best_url(a) for a in message.attachments]
        try:
            if not args:
                raise ArgumentError
        except ArgumentError:
            if not args:
                url = None
                try:
                    url = await bot.get_last_image(message.channel)
                except FileNotFoundError:
                    raise ArgumentError("Please input an image by URL or attachment.")
            else:
                raise ArgumentError("Please input an image by URL or attachment.")
        if name in ("frames", "imagesequence"):
            fmt = "zip"
        elif args[-1] in VIDEOS:
            fmt = args.pop(-1)
        else:
            fmt = "gif"
        if "r" in flags or args[-1].isnumeric():
            fr = args.pop(-1)
            rate = await bot.eval_math(fr)
        else:
            rate = None
        # Validate framerate values to prevent issues further down the line
        if rate and rate <= 0:
            args = args[:1]
            rate = 1
        delay = round(1000 / rate) if rate else None
        if delay and delay <= 0:
            args = args[-1:]
            delay = 1000
        elif delay and delay >= 16777216:
            raise OverflowError("GIF image framerate too low.")
        with discord.context_managers.Typing(channel):
            video = None
            for i, url in enumerate(args):
                urls = await bot.follow_url(url, best=True, allow=True, limit=1)
                url = urls[0]
                if "discord" not in url and "channels" not in url:
                    with tracebacksuppressor:
                        url, size, dur, fps = await create_future(get_video, url, None, timeout=60)
                        if size and dur and fps:
                            video = (url, size, dur, fps)
                if not url:
                    raise ArgumentError(f'Invalid URL detected: "{url}".')
                args[i] = url
            filename = "unknown." + fmt
            if video is None:
                video = args
            resp = await process_image("create_gif", "$", ["image", args, delay, "-f", fmt], timeout=_timeout)
            fn = resp[0]
        await bot.send_with_file(channel, "", fn, filename=filename, reference=message)


class Resize(Command):
    name = ["ImageScale", "Scale", "Rescale", "ImageResize","리사이즈","사이즈조정"]
    description = "이미지의 크기를 조정합니다. "
    usage = "<0:이미지url> <1:x_multiplier(1)>? <2:y_multiplier(x)>? (nearest|linear|hamming|bicubic|lanczos|scale2x|crop|auto)?"
    no_parse = True
    rate_limit = (3, 6)
    flags = "l"
    _timeout_ = 4
    typing = True

    async def __call__(self, bot, user, guild, channel, message, flags, args, argv, _timeout, **void):
        # Take input from any attachments, or otherwise the message contents
        if message.attachments:
            args = [best_url(a) for a in message.attachments] + args
            argv = " ".join(best_url(a) for a in message.attachments) + " " * bool(argv) + argv
        if not args or argv == "list":
            if "l" in flags or argv == "list":
                return ini_md("Available scaling operations: [nearest, linear, hamming, bicubic, lanczos, scale2x, crop, auto]")
            # raise ArgumentError("Please input an image by URL or attachment.")
        with discord.context_managers.Typing(channel):
            try:
                url = args.pop(0)
                urls = await bot.follow_url(url, best=True, allow=True, limit=1)
                if not urls:
                    urls = await bot.follow_to_image(argv)
                    if not urls:
                        urls = await bot.follow_to_image(url)
                        if not urls:
                            raise ArgumentError
                url = urls[0]
            except (LookupError, ArgumentError):
                if not argv:
                    url = None
                    try:
                        url = await bot.get_last_image(message.channel)
                    except FileNotFoundError:
                        raise ArgumentError("Please input an image by URL or attachment.")
                else:
                    raise ArgumentError("Please input an image by URL or attachment.")
            value = " ".join(args).strip()
            func = "resize_mult"
            fmt2 = url.split("?", 1)[0].rsplit(".", 1)[-1]
            if fmt2 not in ("mp4", "gif"):
                if is_url(url):
                    resp = await create_future(requests.head, url)
                    fmt2 = resp.headers["Content-Type"].rsplit("/", 1)[-1]
                    if fmt2 not in ("mp4", "gif"):
                        fmt2 = "mp4"
                else:
                    fmt2 = "mp4"
            if not value:
                x = y = 1
                op = "auto"
                fmt = fmt2
            else:
                # Parse width and height multipliers
                if "x" in value[:-1] or "X" in value or "*" in value or "×" in value:
                    func = "resize_to"
                    value = value.replace("x", " ").replace("X", " ").replace("*", " ").replace("×", " ")
                else:
                    value = value.replace(":", " ")
                try:
                    spl = smart_split(value)
                except ValueError:
                    spl = value.split()
                x = await bot.eval_math(spl.pop(0))
                if spl:
                    y = await bot.eval_math(spl.pop(0))
                else:
                    y = x
                if func == "resize_mult":
                    for value in (x, y):
                        if not value >= -32 or not value <= 32:
                            raise OverflowError("Maximum multiplier input is 32.")
                if spl:
                    op = spl.pop(0)
                    if op == "scale2":
                        op = "scale2x"
                else:
                    op = "auto"
                if spl:
                    fmt = spl.pop(0)
                else:
                    fmt = fmt2
            # Try and find a good name for the output image
            try:
                name = url[url.rindex("/") + 1:]
                if not name:
                    raise ValueError
                if "." in name:
                    name = name[:name.rindex(".")]
            except ValueError:
                name = "unknown"
            if not name.endswith("." + fmt):
                name += "." + fmt
            resp = await process_image(url, func, [x, y, op, "-f", fmt], timeout=_timeout)
            fn = resp[0]
            if fn.endswith(".mp4"):
                if not name.endswith(".mp4"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".mp4"
            elif fn.endswith(".png"):
                if not name.endswith(".png"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".png"
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Rotate(Command):
    name = ["Orientate", "Orientation", "Transpose","회전","로테이트"]
    description = "이미지를 회전시킵니다."
    usage = "<0:이미지url> <1:각도(90)>?"
    no_parse = True
    rate_limit = (2, 5)
    _timeout_ = 3
    typing = True

    async def __call__(self, bot, user, channel, message, args, argv, _timeout, **void):
        name, value, url, fmt = await get_image(bot, user, message, args, argv, default=90, raw=True)
        value = await bot.eval_math(value)
        with discord.context_managers.Typing(channel):
            resp = await process_image(url, "rotate_to", [value, "-f", fmt], timeout=_timeout)
            fn = resp[0]
            if fn.endswith(".gif"):
                if not name.endswith(".gif"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".gif"
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Fill(Command):
    name = ["ImageFill", "FillChannel", "FillImage","채우기"]
    description = "이미지를 선택한 값으로 채웁니다."
    usage = "<0:이미지url> [rgbcmyhsva]* <-1:값(0)>?"
    no_parse = True
    rate_limit = (3, 6)
    flags = "l"
    _timeout_ = 3
    typing = True

    async def __call__(self, bot, user, guild, channel, message, flags, args, argv, _timeout, **void):
        # Take input from any attachments, or otherwise the message contents
        if message.attachments:
            args = [best_url(a) for a in message.attachments] + args
            argv = " ".join(best_url(a) for a in message.attachments) + " " * bool(argv) + argv
        try:
            if not args:
                raise ArgumentError
            url = args.pop(0)
            urls = await bot.follow_url(url, best=True, allow=True, limit=1)
            if not urls:
                urls = await bot.follow_to_image(argv)
                if not urls:
                    urls = await bot.follow_to_image(url)
                    if not urls:
                        raise ArgumentError
            url = urls[0]
        except ArgumentError:
            if not argv:
                url = None
                try:
                    url = await bot.get_last_image(message.channel)
                except FileNotFoundError:
                    raise ArgumentError("Please input an image by URL or attachment.")
            else:
                raise ArgumentError("Please input an image by URL or attachment.")
        with discord.context_managers.Typing(channel):
            if is_numeric(args[-1]):
                value = await bot.eval_math(args.pop(-1))
                if type(value) is not int:
                    if abs(value) <= 1:
                        value = round(value * 255)
                    else:
                        raise ValueError("invalid non-integer input value.")
            else:
                value = 255
            if not args:
                args = "rgb"
            # Try and find a good name for the output image
            try:
                name = url[url.rindex("/") + 1:]
                if not name:
                    raise ValueError
                if "." in name:
                    name = name[:name.rindex(".")]
            except ValueError:
                name = "unknown"
            if not name.endswith(".png"):
                name += ".png"
            resp = await process_image(url, "fill_channels", [value, *args], timeout=_timeout)
            fn = resp[0]
            if fn.endswith(".gif"):
                if not name.endswith(".gif"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".gif"
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Blend(Command):
    name = ["ImageBlend", "ImageOP","혼합"]
    description = "두 이미지를 결합합니다."
    usage = "<0:이미지url1> <1:이미지url2> (normal|replace|add|sub|mul|div|mod|and|or|xor|nand|nor|xnor|difference|overlay|screen|soft|hard|lighten|darken|plusdarken|overflow|lighting|burn|linearburn|dodge|hue|sat|lum|colour|extract|merge)? <3:opacity(0.5|1)>?"
    no_parse = True
    rate_limit = (3, 8)
    flags = "l"
    _timeout_ = 7
    typing = True

    async def __call__(self, bot, user, guild, channel, message, flags, args, argv, _timeout, **void):
        # Take input from any attachments, or otherwise the message contents
        if message.attachments:
            args = [best_url(a) for a in message.attachments] + args
            argv = " ".join(best_url(a) for a in message.attachments) + " " * bool(argv) + argv
        if not args or argv == "list":
            if "l" in flags or argv == "list":
                return ini_md(
                    "Available blend operations: ["
                    + "replace, add, sub, mul, div, mod, and, or, xor, nand, nor, xnor, "
                    + "difference, overlay, screen, soft, hard, lighten, darken, plusdarken, overflow, lighting, "
                    + "burn, linearburn, dodge, lineardodge, hue, sat, lum, colour, extract, merge]"
                )
            raise ArgumentError("Please input an image by URL or attachment.")
        with discord.context_managers.Typing(channel):
            urls = await bot.follow_url(args.pop(0), best=True, allow=True, limit=1)
            if urls:
                url1 = urls[0]
            else:
                url1 = None
            if not args:
                raise ArgumentError("This command requires two image inputs as URL or attachment.")
            urls = await bot.follow_url(args.pop(0), best=True, allow=True, limit=1)
            if urls:
                url2 = urls[0]
            else:
                url1 = None
            fromA = False
            if not url1 or not url2:
                urls = await bot.follow_to_image(argv)
                if not urls:
                    urls = await bot.follow_to_image(argv)
                    if not urls:
                        raise ArgumentError("Please input an image by URL or attachment.")
                if type(urls) not in (list, alist):
                    urls = alist(urls)
                if not url1:
                    url1 = urls.pop(0)
                if not url2:
                    url2 = urls.pop(0)
            if fromA:
                value = argv
            else:
                value = " ".join(args).strip()
            if not value:
                opacity = 0.5
                operation = "replace"
            else:
                try:
                    spl = smart_split(value)
                except ValueError:
                    spl = value.split()
                operation = spl.pop(0)
                if spl:
                    opacity = await bot.eval_math(spl.pop(-1))
                else:
                    opacity = 1
                if not opacity >= -256 or not opacity <= 256:
                    raise OverflowError("Maximum multiplier input is 256.")
                if spl:
                    operation += " ".join(spl)
                if not operation:
                    operation = "replace"
            # Try and find a good name for the output image
            try:
                name = url1[url1.rindex("/") + 1:]
                if not name:
                    raise ValueError
                if "." in name:
                    name = name[:name.rindex(".")]
            except ValueError:
                name = "unknown"
            if not name.endswith(".png"):
                name += ".png"
            resp = await process_image(url1, "blend_op", [url2, operation, opacity], timeout=_timeout)
            print(resp)
            fn = resp[0]
            if fn.endswith(".gif"):
                if not name.endswith(".gif"):
                    if "." in name:
                        name = name[:name.rindex(".")]
                    name += ".gif"
        await bot.send_with_file(channel, "", fn, filename=name, reference=message)


class Steganography(Command):
    name = ["Watermark", "Copyright", "Ownership", "NFT", "C", "©","태그","태그지정"]
    description = "이미지에 사용자 또는 메시지 태그를 지정합니다(다른 사용자에 태그를 지정하려면 사용자 ID 입력). 이미지에 이미 태그가 있는 경우 오류가 발생합니다."
    usage = "<0:이미지url> <1:데이터>? <2:메시지>?"
    no_parse = True
    rate_limit = (1, 5)
    _timeout_ = 6
    typing = True

    async def __call__(self, bot, user, message, channel, args, name, **void):
        for a in message.attachments:
            args.insert(0, a.url)
        ts = ts_us()
        if not args:
            raise ArgumentError("Please input an image by URL or attachment.")
        urls = await bot.follow_url(args.pop(0))
        if not urls:
            raise ArgumentError("Please input an image by URL or attachment.")
        url = urls[0]
        b = await bot.get_request(url)
        if name == "nft":
            await bot.silent_delete(message)
        if args:
            msg = args.pop(0)
            n = verify_id(msg)
            if isinstance(n, int):
                try:
                    user = await bot.fetch_user(n)
                except:
                    pass
                else:
                    msg = str(user.id)
        else:
            msg = str(user.id)
        remsg = " ".join(args)
        args = (
            sys.executable,
            "misc/steganography.py",
            f"cache/{ts}.png",
            msg,
        )
        fon = url.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        with discord.context_managers.Typing(channel):
            with open(f"cache/{ts}.png", "wb") as f:
                await create_future(f.write, b)
            print(args)
            proc = psutil.Popen(args, cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                await create_future(proc.wait, timeout=3200)
            except (T0, T1, T2):
                with tracebacksuppressor:
                    force_kill(proc)
                raise
            else:
                text = proc.stdout.read().decode("utf-8", "replace").strip()
                if text.startswith("Copyright detected"):
                    i = text.split(": ", 1)[-1]
                    if i.isnumeric():
                        i = int(i)
                        try:
                            u = await bot.fetch_user(i)
                        except:
                            pass
                        else:
                            pe = PermissionError(f"Copyright detected; image belongs to {user_mention(u.id)}")
                            pe.no_react = True
                            raise pe
                    pe = PermissionError(text)
                    pe.no_react = True
                    raise pe
        fn = f"cache/{ts}~1.png"
        if name == "nft":
            f = CompatFile(fn, filename=f"{fon}.png")
            url = await self.bot.get_proxy_url(user)
            await self.bot.send_as_webhook(message.channel, remsg, files=[f], username=user.display_name, avatar_url=url)
        else:
            await bot.send_with_file(channel, f'Successfully created image with encoded message "{msg}".', fn, filename=f"{fon}.png", reference=message)

    async def _callback_(self, bot, message, reaction, user, vals, **void):
        u_id, c_id, m_id = map(int, vals.split("_", 2))
        if user.id != u_id:
            return
        if reaction.decode("utf-8", "replace") != "🗑️":
            return
        m = message
        channel = await bot.fetch_channel(c_id)
        message = await bot.fetch_message(m_id, channel)
        await bot.silent_delete(message)
        guild = message.guild
        if guild and "logM" in bot.data and guild.id in bot.data.logM:
            c_id = bot.data.logM[guild.id]
            try:
                c = await self.bot.fetch_channel(c_id)
            except (EOFError, discord.NotFound):
                bot.data.logM.pop(guild.id)
                return
            emb = await bot.as_embed(message, link=True)
            emb.colour = discord.Colour(0x00FF00)
            action = f"{user_mention(u_id)} **deleted a copyrighted image deleted from** {channel_mention(channel.id)}:\n"
            emb.description = lim_str(action + emb.description, 4096)
            emb.timestamp = message.created_at
            self.bot.send_embeds(c, emb)
        await m.reply("Message has been successfully taken down.")


class Waifu2x(Command):
    name=["와이프리사이즈","Waifu리사이즈"]
    description = "Waifu2x AI 알고리즘을 사용하여 대상 이미지의 크기를 조정합니다."
    usage = "<이미지url> <api{?a}>"
    no_parse = True
    rate_limit = (5, 10)
    flags = "l"
    _timeout_ = 5
    typing = True

    async def __call__(self, bot, user, message, channel, args, argv, flags, **void):
        name, value, url, fmt = await get_image(bot, user, message, args, argv, raw=True, default="")
        if "a" not in flags:
            return self.bot.webserver + "/waifu2x?source=" + url
        with discord.context_managers.Typing(channel):
            mime = await create_future(bot.detect_mime, url)
            image = None
            if "image/png" not in mime:
                if "image/jpg" not in mime:
                    if "image/jpeg" not in mime:
                        resp = await process_image(url, "resize_mult", ["-nogif", 1, 1, "auto"], timeout=60)
                        with open(resp[0], "rb") as f:
                            image = await create_future(f.read)
                        ext = "png"
                    else:
                        ext = "jpeg"
                else:
                    ext = "jpg"
            else:
                ext = "png"
            if not image:
                image = await Request(url, timeout=20, aio=True)
            data = await create_future(
                Request,
                "https://api.alcaamado.es/api/v1/waifu2x/convert",
                files={
                    "denoise": (None, "1"),
                    "scale": (None, "true"),
                    "file": (f"file.{ext}", image),
                },
                _timeout_=22,
                method="post",
                json=True,
            )
            for i in range(60):
                async with Delay(0.75):
                    img = await Request(
                        f"https://api.alcaamado.es/api/v1/waifu2x/get?hash={data['hash']}",
                        headers=dict(Accept="application/json, text/plain, */*"),
                        timeout=60,
                        json=True,
                        aio=True,
                    )
                    if img.get("image"):
                        break
            if not img.get("image"):
                raise FileNotFoundError("image file not found")
            image = await create_future(base64.b64decode, img["image"])
        await bot.send_with_file(channel, "", file=image, filename=name, reference=message)


class StableDiffusion(Command):
    _timeout_ = 150
    name = ["Art", "AIArt", "Inpaint","아트","AI아트"]
    description = "입력 프롬프트 또는 이미지에서 안정적 확산 AI 아트 생성기를 실행합니다. 글로벌 대기열 시스템에서 작동합니다. 적절한 키워드 인수를 사용합니다."
    usage = "<0:프롬프트> <inpaint{?i}>"
    rate_limit = (12, 60)
    flags = "i"
    typing = True
    slash = ("Art",)
    sdiff_sem = Semaphore(1, 256, rate_limit=1)
    fut = None
    imagebot = imagebot.Bot()

    async def __call__(self, bot, channel, message, name, args, flags, **void):
        for a in reversed(message.attachments):
            args.insert(0, a.url)
        if not args:
            raise ArgumentError("Input string is empty.")
        req = " ".join(args)
        url = None
        url2 = None
        rems = deque()
        kwargs = {
            "--num-inference-steps": "24",
            "--guidance-scale": "7.5",
            "--eta": "0.8",
        }
        inpaint = "i" in flags or name == "inpaint"
        specified = set()
        aspect = 1
        kwarg = ""
        for arg in args:
            if kwarg:
                # if kwarg == "--model":
                #     kwargs[kwarg] = arg
                if kwarg == "--seed":
                    kwargs[kwarg] = arg
                elif kwarg in ("--num-inference-steps", "--ddim_steps"):
                    kwarg = "--num-inference-steps"
                    kwargs[kwarg] = str(max(1, min(64, int(arg))))
                elif kwarg in ("--guidance-scale", "--scale"):
                    kwarg = "--guidance-scale"
                    kwargs[kwarg] = str(max(0, min(100, float(arg))))
                elif kwarg == "--eta":
                    kwargs[kwarg] = str(max(0, min(1, float(arg))))
                # elif kwarg in ("--tokenizer", "--tokeniser"):
                #     kwargs["--tokenizer"] = arg
                elif kwarg == "--prompt":
                    kwargs[kwarg] = arg
                elif kwarg == "--strength":
                    kwargs[kwarg] = str(max(0, min(1, float(arg))))
                elif kwarg == "--aspect-ratio":
                    aspect = float(arg)
                # elif kwargs == "--mask":
                #     kwargs[kwarg] = arg
                specified = kwarg
                kwarg = ""
                continue
            if arg.startswith("--"):
                kwarg = arg
                continue
            urls = None
            i = verify_id(arg)
            if isinstance(i, int):
                with suppress():
                    u = await bot.fetch_user(i)
                    rems.append(u.display_name)
                    urls = [best_url(u)]
            if not urls:
                urls = await bot.follow_url(arg, allow=True, images=True)
                if not urls:
                    rems.append(arg)
                else:
                    urls = list(urls)
            if urls and not url:
                url = urls.pop(0)
            if urls and not url2:
                url2 = urls.pop(0)
        if not self.fut and not os.path.exists("misc/stable_diffusion.openvino"):
            self.fut = create_future(subprocess.run(
                [
                    "git",
                    "clone",
                    "https://github.com/bes-dev/stable_diffusion.openvino.git",
                ],
                cwd="misc",
            ))
        prompt = " ".join(rems).strip()
        if not prompt:
            if not url:
                raise ArgumentError("Please input a valid prompt.")
            if TrOCRProcessor:
                processor = await create_future(TrOCRProcessor.from_pretrained, "nlpconnect/vit-gpt2-image-captioning")
                model = await create_future(VisionEncoderDecoderModel.from_pretrained, "nlpconnect/vit-gpt2-image-captioning")
                b = await bot.get_request(url)
                with tracebacksuppressor:
                    image = Image.open(io.BytesIO(b)).convert("RGB")
                    pixel_values = processor(image, return_tensors="pt").pixel_values
                    generated_ids = await create_future(model.generate, pixel_values)
                    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                    prompt = generated_text.strip()
            if not prompt:
                prompt = "art"
            print(url, prompt)
        req = prompt
        if url:
            if req:
                req += " "
            req += url
            if url2:
                req += " " + url2
        if specified:
            req += " ".join(f"{k} {v}" for k, v in kwargs.items() if k in specified)
        fn = None
        with discord.context_managers.Typing(channel):
            with tracebacksuppressor:
                fn = await create_future(self.imagebot.art, prompt, url, url2, kwargs, specified, timeout=60)
        if not fn:
            if self.fut:
                with tracebacksuppressor:
                    await self.fut
                    if os.name == "nt":
                        self.fut = create_future(subprocess.run(
                            [
                                "py",
                                "-3.9",
                                "-m",
                                "pip",
                                "install",
                                "-r",
                                "requirements.txt",
                            ],
                            cwd="misc",
                        ))
                    else:
                        self.fut = create_future(subprocess.run(
                            [
                                sys.executable,
                                "-m",
                                "pip",
                                "install",
                                "-r",
                                "requirements.txt",
                            ],
                            cwd="misc",
                        ))
                    await self.fut
                    self.fut = None
            if os.name == "nt":
                args = [
                    "py",
                    "-3.9",
                    "demo.py",
                ]
            else:
                args = [
                    sys.executable,
                    "demo.py",
                ]
            if prompt and "--prompt" not in kwargs:
                args.extend((
                    "--prompt",
                    prompt,
                ))
            with discord.context_managers.Typing(channel):
                if self.sdiff_sem.is_busy() and not getattr(message, "simulated", False):
                    await send_with_react(channel, italics(ini_md(f"StableDiffusion: {sqr_md(req)} enqueued in position {sqr_md(self.sdiff_sem.passive + 1)}.")), reacts="❎", reference=message)
                async with self.sdiff_sem:
                    if url:
                        fn = "misc/stable_diffusion.openvino/input.png"
                        resp = await process_image(url, "resize_to", ["-nogif", 512, 512, "auto"], timeout=60)
                        if os.path.exists(fn):
                            os.remove(fn)
                        os.rename(resp[0], fn)
                        args.extend((
                            "--init-image",
                            "input.png",
                        ))
                        if inpaint and url2:
                            b = await bot.get_request(url2)
                            fm = "misc/stable_diffusion.openvino/mask.png"
                            with open(fm, "wb") as f:
                                f.write(b)
                            args.extend((
                                "--mask",
                                "mask.png",
                            ))
                        if inpaint and not url2:
                            fm = "misc/stable_diffusion.openvino/mask.png"
                            resp = await process_image(fn, "get_mask", ["-nogif", "-nodel"], timeout=60)
                            if os.path.exists(fm):
                                os.remove(fm)
                            os.rename(resp[0], fm)
                            resp = await process_image(fn, "inpaint", [fm, "-nodel"], timeout=60)
                            if os.path.exists(fn):
                                os.remove(fn)
                            os.rename(resp[0], fn)
                            resp = await process_image(fm, "expand_mask", ["-nogif", 12], timeout=60)
                            if os.path.exists(fm):
                                os.remove(fm)
                            os.rename(resp[0], fm)
                            args.extend((
                                "--mask",
                                "mask.png",
                            ))
                            # if "--strength" not in kwargs:
                            #     args.extend((
                            #         "--strength",
                            #         "1",
                            #     ))
                        if "--strength" not in kwargs:
                            args.extend((
                                "--strength",
                                "0.75",
                            ))
                    for k, v in kwargs.items():
                        args.extend((k, v))
                    print(args)
                    proc = await asyncio.create_subprocess_exec(*args, cwd=os.getcwd() + "/misc/stable_diffusion.openvino", stdout=subprocess.DEVNULL)
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=3200)
                    except (T0, T1, T2):
                        with tracebacksuppressor:
                            force_kill(proc)
                        raise
            fn = "misc/stable_diffusion.openvino/output.png"
        await bot.send_with_file(channel, "", fn, filename=lim_str(prompt, 96) + ".png", reference=message, reacts="🔳")


class UpdateImages(Database):
    name = "images"
