class AutoEmoji(Command):
    server_only = True
    name = ["NQN", "Emojis", "이모티콘"]
    min_level = 0
    description = "Causes all failed emojis starting and ending with : to be deleted and reposted with a webhook, when possible."
    usage = "(가능|불가능)?"
    flags = "aed"
    directions = [b'\xe2\x8f\xab', b'\xf0\x9f\x94\xbc', b'\xf0\x9f\x94\xbd', b'\xe2\x8f\xac', b'\xf0\x9f\x94\x84']
    dirnames = ["First", "Prev", "Next", "Last", "Refresh"]
    rate_limit = 1

    async def __call__(self, bot, flags, guild, message, user, name, perm, **void):
        data = bot.data.autoemojis
        if flags and perm < 3:
            reason = guild.name + "에 대한 자동 이모티콘을 수정하기위해"
            raise self.perm_error(perm, 3, reason)
        if "e" in flags or "a" in flags:
            data[guild.id] = True
            return italics(css_md(f"{sqr_md(guild)}에 대한 자동 이모티콘 대체 활성화."))
        elif "d" in flags:
            data.pop(guild.id, None)
            return italics(css_md(f"{sqr_md(guild)}에 대한 자동 이모티콘 대체 비활성화."))
        buttons = [cdict(emoji=dirn, name=name, custom_id=dirn) for dirn, name in zip(map(as_str, self.directions), self.dirnames)]
        await send_with_reply(
            None,
            message,
            "*```" + "\n" * ("z" in flags) + "callback-webhook-autoemoji-"
            + str(user.id) + "_0"
            + "-\nAutoEmoji 데이터베이스 로드중...```*",
            buttons=buttons,
        )
    
    async def _callback_(self, bot, message, reaction, user, perm, vals, **void):
        u_id, pos = list(map(int, vals.split("_", 1)))
        if reaction not in (None, self.directions[-1]) and u_id != user.id and perm < 3:
            return
        if reaction not in self.directions and reaction is not None:
            return
        guild = message.guild
        user = await bot.fetch_user(u_id)
        data = bot.data.autoemojis
        curr = {f":{e.name}:": f"({e.id})` {min_emoji(e)}" for e in sorted(guild.emojis, key=lambda e: full_prune(e.name)) if e.is_usable()}
        page = 16
        last = max(0, len(curr) - page)
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
        content = "```" + "\n" * ("\n" in content[:i]) + (
            "callback-webhook-autoemoji-"
            + str(u_id) + "_" + str(pos)
            + "-\n"
        )
        if guild.id in data:
            content += f"자동 이모티콘 대체는 현재 {sqr_md(guild)}에서 활성화되어 있습니다.```"
        else:
            content += f'자동 이모티콘 대체는 현재 {sqr_md(guild)}에서 비활성화되어 있습니다. 활성화 하려면"{bot.get_prefix(guild)}autoemoji enable"을 사용하십시오.```'
        if not curr:
            msg = italics(code_md(f"{str(message.guild).replace('`', '')}에 대한 맞춤 이모티콘을 찾을 수 없습니다."))
        else:
            msg = italics(code_md(f"현재 {str(message.guild).replace('`', '')}에 할당된{len(curr)}개의 맞춤 이모티콘:")) + "\n" + iter2str({k + " " * (32 - len(k)): curr[k] for k in tuple(curr)[pos:pos + page]}, left="`", right="")
        colour = await self.bot.get_colour(guild)
        emb = discord.Embed(
            description=msg,
            colour=colour,
        )
        emb.set_author(**get_author(user))
        more = len(curr) - pos - page
        if more > 0:
            emb.set_footer(text=f"{uni_str('And', 1)} {more} {uni_str('more...', 1)}")
        create_task(message.edit(content=content, embed=emb))
        if hasattr(message, "int_token"):
            await bot.ignore_interaction(message)


class UpdateAutoEmojis(Database):
    name = "autoemojis"

    def guild_emoji_map(self, guild, emojis={}):
        for e in sorted(guild.emojis, key=lambda e: e.id):
            if not e.is_usable():
                continue
            n = e.name
            while n in emojis:
                if emojis[n] == e.id:
                    break
                t = n.rsplit("-", 1)
                if t[-1].isnumeric():
                    n = t[0] + "-" + str(int(t[-1]) + 1)
                else:
                    n = t[0] + "-1"
            emojis[n] = e
        return emojis

    async def _nocommand_(self, message, recursive=True, edit=False, **void):
        if edit or not message.content or getattr(message, "webhook_id", None) or message.content.count("```") > 1:
            return
        emojis = find_emojis(message.content)
        for e in emojis:
            name, e_id = e.split(":")[1:]
            e_id = int("".join(regexp("[0-9]+").findall(e_id)))
            animated = self.bot.cache.emojis.get(name)
            if not animated:
                animated = await create_future(self.bot.is_animated, e_id, verify=True)
            else:
                name = animated.name
            if animated is not None and not message.webhook_id:
                orig = self.bot.data.emojilists.setdefault(message.author.id, {})
                orig[name] = e_id
                self.bot.data.emojilists.update(message.author.id)
        if not message.guild or message.guild.id not in self.data:
            return
        m_id = None
        msg = message.content
        guild = message.guild
        orig = self.bot.data.emojilists.get(message.author.id, {})
        emojis = None
        # long = len(msg) > 32
        if msg.startswith("+"):
            emi = msg[1:].strip()
            spl = emi.rsplit(None, 1)
            if len(spl) > 1:
                ems, m_id = spl
                if not m_id.isnumeric():
                    spl = [emi]
            if len(spl) == 1:
                ems = spl[0]
                m2 = await self.bot.history(message.channel, limit=1, before=message.id).__anext__()
            else:
                m2 = None
                if m_id:
                    m_id = int(m_id)
            if not m2 and m_id:
                try:
                    m2 = await self.bot.fetch_message(m_id, message.channel)
                except LookupError:
                    m2 = None
            if m2:
                futs = deque()
                ems = regexp("<a?:[A-Za-z0-9\\-~_]{1,32}").sub("", ems.replace(" ", "").replace("\\", "")).replace(">", ":")
                possible = regexp(":[A-Za-z0-9\\-~_]{1,32}:|[^\\x00-\\x7F]").findall(ems)
                s = ems
                for word in possible:
                    s = s.replace(word, "")
                if s.strip():
                    return
                possible = (n.strip(":") for n in possible)
                for name in (n for n in possible if n):
                    emoji = None
                    if emojis is None:
                        emojis = self.guild_emoji_map(guild, dict(orig))
                    if ord(name[0]) >= 128:
                        emoji = name
                    else:
                        emoji = emojis.get(name)
                    if not emoji:
                        r1 = regexp("^[A-Za-z0-9\\-~_]{1,32}$")
                        if r1.fullmatch(name):
                            if name.isnumeric():
                                emoji = int(name)
                            else:
                                t = name[::-1].replace("~", "-", 1)[::-1].rsplit("-", 1)
                                if t[-1].isnumeric():
                                    i = int(t[-1])
                                    if i < 1000:
                                        if not emoji:
                                            name = t[0]
                                            emoji = emojis.get(name)
                                        while i > 1 and not emoji:
                                            i -= 1
                                            name = t[0] + "-" + str(i)
                                            emoji = emojis.get(name)
                    if emoji:
                        if type(emoji) is int:
                            e_id = await self.bot.id_from_message(emoji)
                            emoji = self.bot.cache.emojis.get(e_id)
                        futs.append(create_task(m2.add_reaction(emoji)))
                if futs:
                    futs.append(create_task(self.bot.silent_delete(message)))
                    for fut in futs:
                        await fut
                    return
        if message.content.count(":") < 2:
            return
        regex = regexp("(?:^|^[^<\\\\`]|[^<][^\\\\`]|.[^a\\\\`])(:[A-Za-z0-9\\-~_]{1,32}:)(?:(?![^0-9]).)*(?:$|[^0-9>`])")
        pops = set()
        offs = 0
        while offs < len(msg):
            matched = regex.search(msg[offs:])
            if not matched:
                break
            substitutes = None
            s = matched.group()
            start = matched.start()
            while s and not regexp(":[A-Za-z0-9\\-~_]").fullmatch(s[:2]):
                s = s[1:]
                start += 1
            while s and not regexp("[A-Za-z0-9\\-~_]:").fullmatch(s[-2:]):
                s = s[:-1]
            offs = start = offs + start
            offs += len(s)
            if not s:
                continue
            name = s[1:-1]
            if emojis is None:
                emojis = self.guild_emoji_map(guild, dict(orig))
            emoji = emojis.get(name)
            if not emoji:
                if name.isnumeric():
                    emoji = int(name)
                else:
                    t = name[::-1].replace("~", "-", 1)[::-1].rsplit("-", 1)
                    if t[-1].isnumeric():
                        i = int(t[-1])
                        if i < 1000:
                            if not emoji:
                                name = t[0]
                                emoji = emojis.get(name)
                            while i > 1 and not emoji:
                                i -= 1
                                name = t[0] + "-" + str(i)
                                emoji = emojis.get(name)
            if type(emoji) is int:
                e_id = await self.bot.id_from_message(emoji)
                emoji = self.bot.cache.emojis.get(e_id)
                if not emoji:
                    animated = await create_future(self.bot.is_animated, e_id, verify=True)
                    if animated is not None:
                        emoji = cdict(id=e_id, animated=animated)
                if not emoji and not message.webhook_id:
                    self.bot.data.emojilists.get(message.author.id, {}).pop(name, None)
                    self.bot.data.emojilists.update(message.author.id)
            if emoji:
                pops.add((str(name), emoji.id))
                if len(msg) < 1936:
                    sub = "<"
                    if emoji.animated:
                        sub += "a"
                    name = getattr(emoji, "name", None) or "_"
                    sub += f":{name}:{emoji.id}>"
                else:
                    sub = min_emoji(emoji)
                substitutes = (start, sub, start + len(s))
                if getattr(emoji, "name", None):
                    if not message.webhook_id:
                        orig = self.bot.data.emojilists.setdefault(message.author.id, {})
                        orig.setdefault(name, emoji.id)
                        self.bot.data.emojilists.update(message.author.id)
            if substitutes:
                msg = msg[:substitutes[0]] + substitutes[1] + msg[substitutes[2]:]
        if not msg or msg == message.content:
            return
        msg = escape_everyone(msg).strip("\u200b")
        if not msg or msg == message.content or len(msg) > 2000:
            return
        if not recursive:
            return msg
        files = deque()
        for a in message.attachments:
            b = await self.bot.get_request(a.url, full=False)
            files.append(CompatFile(seq(b), filename=a.filename))
        create_task(self.bot.silent_delete(message))
        url = await self.bot.get_proxy_url(message.author)
        m = await self.bot.send_as_webhook(message.channel, msg, files=files, username=message.author.display_name, avatar_url=url)
        if recursive and regex.search(m.content):
            m = await m.edit(content=msg)
            print(m, m.content)
            if m.content == ":_:":
                if emoji:
                    fmt = "gif" if emoji.animated else "png"
                    url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{fmt}?quality=lossless&size=48"
                    await m.edit(content=url)
                    self.pop(m.channel.id)
                    return
            if recursive and regex.search(m.content):
                for k in tuple(pops):
                    if str(k[1]) not in m.content:
                        orig.pop(k[0], None)
                    else:
                        pops.discard(k)
                if pops:
                    print("제거된 이모티콘:", pops)
                    msg = await self._nocommand_(message, recursive=False)
                    if msg:
                        m = await m.edit(content=msg)
                        if m.content == ":_:":
                            if emoji:
                                fmt = "gif" if emoji.animated else "png"
                                url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{fmt}?quality=lossless&size=48"
                                await m.edit(content=url)
                                self.pop(m.channel.id)
                                return
                        if regex.search(m.content):
                            emb = discord.Embed()
                            emb.set_author(**get_author(self.bot.user))
                            emb.description = (
                                "쯧쯧! AutoEmoji가 이모티콘을 변환하지 못한거 같습니다."
                                + "이 문제를 해결하려면 이 서버에 이모티콘을 추가하거나 이모티콘이 있는 서버에 저를 초대하세요, "
                                + "또는 이 채널에 대한 새 webhook를 수동으로 생성하세요!"
                            )
                            await m.edit(embed=emb)
                            self.pop(m.channel.id)
                            self.temp.pop(m.channel.id)
                        # create_task(self.bot.silent_delete(m))
                        # m2 = await self.bot.send_as_webhook(message.channel, msg, files=files, username=message.author.display_name, avatar_url=url)


class EmojiList(Command):
    description = "~autoemoji에서 사용할 수 있는 이모티콘에 대한 사용자 지정 별칭을 설정합니다. 이모지, 이모지 ID, 이모지 URL, 이모지 또는 반응이 포함된 메시지 링크 허용."
    usage = "(추가|삭제)? <이름>? <아이디>?"
    flags = "aed"
    no_parse = True
    directions = [b'\xe2\x8f\xab', b'\xf0\x9f\x94\xbc', b'\xf0\x9f\x94\xbd', b'\xe2\x8f\xac', b'\xf0\x9f\x94\x84']
    dirnames = ["First", "Prev", "Next", "Last", "Refresh"]

    async def __call__(self, bot, flags, message, user, name, argv, args, **void):
        data = bot.data.emojilists
        if "d" in flags:
            try:
                e_id = bot.data.emojilists[user.id].pop(args[0])
            except KeyError:
                raise KeyError(f'이모티콘 이름"{args[0]}"을 찾을 수 없습니다.')
            return italics(css_md(f"{sqr_md(user)}에서 성공적으로 제거된 이모티콘 별칭 {sqr_md(args[0])}: {sqr_md(e_id)}."))
        elif argv:
            try:
                name, e_id = argv.rsplit(None, 1)
            except ValueError:
                raise ArgumentError("별칭 뒤에 이모티콘을 공백으로 구분하여 입력하세요.")
            name = name.strip(":")
            if not regexp("[A-Za-z0-9\\-~_]{1,32}").fullmatch(name):
                raise ArgumentError("이모티콘 별칭에는 1~32자의 영숫자 문자, 대시, 물결표 및 밑줄만 포함할 수 있습니다.")
            e_id = await bot.id_from_message(e_id)
            e_id = as_str(e_id).strip("<>").rsplit(":", 1)[-1].strip(":")
            if not e_id.isnumeric():
                raise ArgumentError("사용자 지정 이모티콘만 지원됩니다.")
            e_id = int(e_id)
            animated = await create_future(bot.is_animated, e_id, verify=True)
            if animated is None:
                raise LookupError(f"이모티콘 {e_id}가 존재하지 않습니다.")
            bot.data.emojilists.setdefault(user.id, {})[name] = e_id
            bot.data.emojilists.update(user.id)
            return ini_md(f"{sqr_md(user)}에서 성공적으로 추가된 이모티콘 별칭 {sqr_md(name)}: {sqr_md(e_id)}.")
        buttons = [cdict(emoji=dirn, name=name, custom_id=dirn) for dirn, name in zip(map(as_str, self.directions), self.dirnames)]
        await send_with_reply(
            None,
            message,
            "*```" + "\n" * ("z" in flags) + "callback-webhook-emojilist-"
            + str(user.id) + "_0"
            + "-\nEmojiList 데이터베이스 로드 중...```*",
            buttons=buttons,
            ephemeral=True,
        )
    
    async def _callback_(self, bot, message, reaction, user, perm, vals, **void):
        u_id, pos = list(map(int, vals.split("_", 1)))
        if reaction not in (None, self.directions[-1]) and u_id != user.id and perm <= inf:
            return
        if reaction not in self.directions and reaction is not None:
            return
        guild = message.guild
        user = await bot.fetch_user(u_id)
        following = bot.data.emojilists
        items = following.get(user.id, {}).items()
        page = 16
        last = max(0, len(items) - page)
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
        curr = {}
        for k, v in sorted(items, key=lambda n: full_prune(n[0]))[pos:pos + page]:
            try:
                try:
                    e = bot.cache.emojis[v]
                    if not e.is_usable():
                        raise LookupError
                    me = " " + str(e)
                except KeyError:
                    await bot.min_emoji(v)
                    me = ""
            except LookupError:
                following[user.id].pop(k)
                following.update(user.id)
                continue
            curr[f":{k}:"] = f"({v})` {me}"
        content = message.content
        if not content:
            content = message.embeds[0].description
        i = content.index("callback")
        content = "*```" + "\n" * ("\n" in content[:i]) + (
            "callback-webhook-emojilist-"
            + str(u_id) + "_" + str(pos)
            + "-\n"
        )
        if not items:
            content += f"현재 {str(user).replace('`', '')}에 할당된 이모티콘 별칭이 없습니다.```*"
            msg = ""
        else:
            content += f"현재 {str(user).replace('`', '')}에 할당된 {len(items)}개의 이모티콘 별칭 :```*"
            key = lambda x: "\n" + ", ".join(x)
            msg = iter2str({k + " " * (32 - len(k)): curr[k] for k in curr}, left="`", right="")
        colour = await self.bot.get_colour(user)
        emb = discord.Embed(
            description=content + msg,
            colour=colour,
        )
        emb.set_author(**get_author(user))
        more = len(curr) - pos - page
        if more > 0:
            emb.set_footer(text=f"{uni_str('And', 1)} {more} {uni_str('more...', 1)}")
        create_task(message.edit(content=None, embed=emb, allowed_mentions=discord.AllowedMentions.none()))
        if hasattr(message, "int_token"):
            await bot.ignore_interaction(message)


class UpdateEmojiLists(Database):
    name = "emojilists"


class MimicConfig(Command):
    name = ["PluralConfig", "RPConfig", "모방속성"]
    description = "기존 웹후크 모방의 속성을 수정합니다."
    usage = "<0:모방_아이디> (접두사|이름|아바타|서술|성별|생일)? <1:새것>?"
    no_parse = True
    rate_limit = 1

    async def __call__(self, bot, user, message, perm, flags, args, **void):
        update = bot.data.mimics.update
        mimicdb = bot.data.mimics
        mimics = set_dict(mimicdb, user.id, {})
        prefix = args.pop(0)
        perm = bot.get_perms(user.id)
        try:
            mlist = mimics[prefix]
            if mlist is None:
                raise KeyError
            mimlist = [bot.get_mimic(verify_id(p)) for p in mlist]
        except KeyError:
            mimic = bot.get_mimic(verify_id(prefix))
            mimlist = [mimic]
        try:
            opt = args.pop(0).casefold()
        except IndexError:
            opt = None
        if opt in ("name", "username", "nickname", "tag"):
            setting = "name"
        elif opt in ("avatar", "icon", "url", "pfp", "image", "img"):
            setting = "url"
        elif opt in ("status", "description"):
            setting = "description"
        elif opt in ("gender", "birthday", "prefix"):
            setting = opt
        elif opt in ("auto", "copy", "user", "auto", "user-id", "user_id"):
            setting = "user"
        elif is_url(opt):
            args = [opt]
            setting = "url"
        elif opt:
            raise TypeError("잘못된 대상 속성.")
        if args:
            new = " ".join(args)
        else:
            new = None
        output = ""
        noret = False
        for mimic in mimlist:
            await bot.data.mimics.update_mimic(mimic, message.guild)
            if mimic.u_id != user.id and not isnan(perm):
                raise PermissionError(f"대상 모방 {mimic.name}은 귀하의 것이 아닙니다.")
            args.extend(best_url(a) for a in message.attachments)
            if new is None:
                if not opt:
                    emb = await bot.commands.info[0].getMimicData(mimic, "v")
                    bot.send_as_embeds(message.channel, emb)
                    noret = True
                else:
                    output += f"{sqr_md(mimic.name)}에 대한 현재 {setting} : {sqr_md(mimic[setting])}.\n"
                continue
            m_id = mimic.id
            if setting == "birthday":
                new = utc_ts(tzparse(new))
            # This limit is actually to comply with webhook usernames
            elif setting == "name":
                if len(new) > 80:
                    raise OverflowError("이름은 80자 이하여야 합니다.")
            # Prefixes must not be too long
            elif setting == "prefix":
                if len(new) > 16:
                    raise OverflowError("접두사의 길이는 16자 이하여야 합니다.")
                for prefix in mimics:
                    with suppress(ValueError, IndexError):
                        mimics[prefix].remove(m_id)
                if new in mimics:
                    mimics[new].append(m_id)
                else:
                    mimics[new] = [m_id]
            elif setting == "url":
                urls = await bot.follow_url(new, best=True)
                new = urls[0]
            # May assign a user to the mimic
            elif setting == "user":
                if new.casefold() in ("none", "null", "0", "false", "f"):
                    new = None
                else:
                    mim = None
                    try:
                        mim = verify_id(new)
                        user = await bot.fetch_user(mim)
                        if user is None:
                            raise EOFError
                        new = user.id
                    except:
                        try:
                            mimi = bot.get_mimic(mim, user)
                            new = mimi.id
                        except:
                            raise LookupError("대상 사용자 또는 모방 ID를 찾을 수 없음.")
            elif setting != "description":
                if len(new) > 512:
                    raise OverflowError("길이는 512 이하여야 합니다.")
            name = mimic.name
            mimic[setting] = new
            update(m_id)
            update(user.id)
        if noret:
            return
        if output:
            return ini_md(output.rstrip())
        return css_md(f"Changed {setting} for {sqr_md(', '.join(m.name for m in mimlist))} to {sqr_md(new)}.")


class Mimic(Command):
    name = ["RolePlay", "Plural", "RP", "RPCreate", "모방"]
    description = "선택적 사용자 이름 및 아이콘 URL을 사용하여 웹후크 모방을 생성하거나 해당 접두사가 있는 모든 모방을 나열합니다. 미믹을 호출하려면 권한 수준 1이 필요합니다."
    usage = "<0:접두사>? <1:사용자|이름>? <2:url[]>? <삭제{?d}>?"
    flags = "aedzf"
    no_parse = True
    directions = [b'\xe2\x8f\xab', b'\xf0\x9f\x94\xbc', b'\xf0\x9f\x94\xbd', b'\xe2\x8f\xac', b'\xf0\x9f\x94\x84']
    dirnames = ["First", "Prev", "Next", "Last", "Refresh"]
    rate_limit = (1, 2)

    async def __call__(self, bot, message, user, perm, flags, args, argv, **void):
        update = self.data.mimics.update
        mimicdb = bot.data.mimics
        args.extend(best_url(a) for a in reversed(message.attachments))
        if len(args) == 1 and "d" not in flags:
            user = await bot.fetch_user(verify_id(argv))
        mimics = set_dict(mimicdb, user.id, {})
        if not argv or (len(args) == 1 and "d" not in flags):
            if "d" in flags:
                # This deletes all mimics for the current user
                if "f" not in flags and len(mimics) > 1:
                    return css_md(sqr_md(f"경고 : {len(mimics)} 모방 대상. 플래그를 확인하기위해 ?F 명령을 반복해라."), force=True)
                mimicdb.pop(user.id)
                return italics(css_md(f"{sqr_md(user)}에 대한 모든 {sqr_md(len(mimics))} webhook 모방을 성공적으로 제거했습니다."))
            # Set callback message for scrollable list
            buttons = [cdict(emoji=dirn, name=name, custom_id=dirn) for dirn, name in zip(map(as_str, self.directions), self.dirnames)]
            await send_with_reply(
                None,
                message,
                "*```" + "\n" * ("z" in flags) + "callback-webhook-mimic-"
                + str(user.id) + "_0"
                + "-\nMimic 데이터베이스 로드 중...```*",
                buttons=buttons,
            )
            return
        u_id = user.id
        prefix = args.pop(0)
        if "d" in flags:
            try:
                mlist = mimics[prefix]
                if mlist is None:
                    raise KeyError
                if len(mlist):
                    m_id = mlist.pop(0)
                    mimic = mimicdb.pop(m_id)
                else:
                    mimics.pop(prefix)
                    update(user.id)
                    raise KeyError
                if not mlist:
                    mimics.pop(prefix)
            except KeyError:
                mimic = bot.get_mimic(prefix, user)
                # Users are not allowed to delete mimics that do not belong to them
                if not isnan(perm) and mimic.u_id != user.id:
                    raise PermissionError("대상 모방은 당신의 것이 아닙니다.")
                mimics = mimicdb[mimic.u_id]
                user = await bot.fetch_user(mimic.u_id)
                m_id = mimic.id
                for prefix in mimics:
                    with suppress(ValueError, IndexError):
                        mimics[prefix].remove(m_id)
                mimicdb.pop(mimic.id)
            update(user.id)
            return italics(css_md(f"{sqr_md(user)}에 대한 webhook 모방 {sqr_md(mimic.name)}을 성공적으로 제거했습니다."))
        if not prefix:
            raise IndexError("접두사는 비워둘 수 없습니다.")
        if len(prefix) > 16:
            raise OverflowError("접두사 길이는 16자 이하여야 합니다.")
        if " " in prefix:
            raise TypeError("접두사에는 공백이 없어야 합니다.")
        # This limit is ridiculous. I like it.
        if sum(len(i) for i in iter(mimics.values())) >= 32768:
            raise OverflowError(f"{user}의 모방 목록이 최대 32768개 항목에 도달했습니다. 다른 항목을 추가하려면 항목을 제거하세요.")
        dop = None
        mid = discord.utils.time_snowflake(dtn())
        ctime = utc()
        m_id = "&" + str(mid)
        mimic = None
        # Attempt to create a new mimic, a mimic from a user, or a copy of an existing mimic.
        if len(args):
            if len(args) > 1:
                urls = await bot.follow_url(args[-1], best=True)
                url = urls[0]
                name = " ".join(args[:-1])
            else:
                mim = 0
                try:
                    mim = verify_id(args[-1])
                    user = await bot.fetch_user(mim)
                    if user is None:
                        raise EOFError
                    dop = user.id
                    name = user.name
                    url = await bot.get_proxy_url(user)
                except:
                    try:
                        mimi = bot.get_mimic(mim, user)
                        dop = mimi.id
                        mimic = copy.deepcopy(mimi)
                        mimic.id = m_id
                        mimic.u_id = u_id
                        mimic.prefix = prefix
                        mimic.count = mimic.total = 0
                        mimic.created_at = ctime
                        mimic.auto = dop
                    except:
                        name = args[0]
                        url = "https://cdn.discordapp.com/embed/avatars/0.png"
        else:
            name = user.name
            url = await bot.get_proxy_url(user)
        # This limit is actually to comply with webhook usernames
        if len(name) > 80:
            raise OverflowError("이름의 길이는 80자 이하여야 합니다.")
        while m_id in mimics:
            mid += 1
            m_id = "&" + str(mid)
        if mimic is None:
            mimic = cdict(
                id=m_id,
                u_id=u_id,
                prefix=prefix,
                auto=dop,
                name=name,
                url=url,
                description="",
                gender="N/A",
                birthday=ctime,
                created_at=ctime,
                count=0,
                total=0,
            )
        mimicdb[m_id] = mimic
        if prefix in mimics:
            mimics[prefix].append(m_id)
        else:
            mimics[prefix] = [m_id]
        update(m_id)
        update(u_id)
        out = f"접두사 {sqr_md(mimic.prefix)} 및 아이디 {sqr_md(mimic.id)}가 있는 webhook 모방 {sqr_md(mimic.name)}을 성공적으로 추가했습니다."
        if dop is not None:
            out += f", bound to user [{user_mention(dop) if type(dop) is int else f'<{dop}>'}]"
        return css_md(out)

    async def _callback_(self, bot, message, reaction, user, perm, vals, **void):
        u_id, pos = list(map(int, vals.split("_", 1)))
        if reaction not in (None, self.directions[-1]) and u_id != user.id and perm <= inf:
            return
        if reaction not in self.directions and reaction is not None:
            return
        guild = message.guild
        update = self.data.mimics.update
        mimicdb = bot.data.mimics
        user = await bot.fetch_user(u_id)
        mimics = mimicdb.get(user.id, {})
        for k in tuple(mimics):
            if not mimics[k]:
                mimics.pop(k)
                update(user.id)
        page = 24
        last = max(0, len(mimics) - page)
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
            "callback-webhook-mimic-"
            + str(u_id) + "_" + str(pos)
            + "-\n"
        )
        if not mimics:
            content += f"현재 {str(user).replace('`', '')}에 대해 활성화된 webhook mimics이 없습니다.```*"
            msg = ""
        else:
            content += f"{str(user).replace('`', '')}에 대해 현재 활성화된 {len(mimics)}개의 webhook 모방:```*"
            key = lambda x: lim_str("⟨" + ", ".join(i + ": " + (str(no_md(mimicdb[i].name)), "[<@" + str(getattr(mimicdb[i], "auto", "None")) + ">]")[bool(getattr(mimicdb[i], "auto", None))] for i in iter(x)) + "⟩", 1900 / len(mimics))
            msg = ini_md(iter2str({k: mimics[k] for k in sorted(mimics)[pos:pos + page]}, key=key))
        colour = await bot.get_colour(user)
        emb = discord.Embed(
            description=content + msg,
            colour=colour,
        )
        emb.set_author(**get_author(user))
        more = len(mimics) - pos - page
        if more > 0:
            emb.set_footer(text=f"{uni_str('And', 1)} {more} {uni_str('more...', 1)}")
        create_task(message.edit(content=None, embed=emb, allowed_mentions=discord.AllowedMentions.none()))
        if hasattr(message, "int_token"):
            await bot.ignore_interaction(message)


class MimicSend(Command):
    name = ["RPSend", "PluralSend", "모방전송"]
    description = "webhook mimic을 사용하여 대상 채널에 메시지를 보냅니다."
    usage = "<0:모방> <1:채널> <2:문자열>"
    no_parse = True
    rate_limit = 0.5

    async def __call__(self, bot, channel, message, user, perm, argv, args, **void):
        update = bot.data.mimics.update
        mimicdb = bot.data.mimics
        mimics = set_dict(mimicdb, user.id, {})
        prefix = args.pop(0)
        c_id = verify_id(args.pop(0))
        channel = await bot.fetch_channel(c_id)
        guild = channel.guild
        msg = argv.split(None, 2)[-1]
        if not msg:
            raise IndexError("메시지가 비어 있습니다.")
        perm = bot.get_perms(user.id, guild)
        try:
            mlist = mimics[prefix]
            if mlist is None:
                raise KeyError
            m = [bot.get_mimic(verify_id(p)) for p in mlist]
        except KeyError:
            mimic = bot.get_mimic(verify_id(prefix))
            m = [mimic]
        admin = not inf > perm
        try:
            enabled = bot.data.enabled[channel.id]
        except KeyError:
            enabled = bot.data.enabled.get(guild.id, ())
        # Because this command operates across channels and servers, we need to make sure these cannot be sent to channels without this command enabled
        if not admin and ("webhook" not in enabled or perm < 1):
            raise PermissionError("대상 채널로 보낼 수 없습니다.")
        if m:
            msg = escape_roles(msg)
            if msg.startswith("/tts "):
                msg = msg[5:]
                tts = True
            else:
                tts = False
            if guild and "logM" in bot.data and guild.id in bot.data.logM:
                c_id = bot.data.logM[guild.id]
                try:
                    c = await self.bot.fetch_channel(c_id)
                except (EOFError, discord.NotFound):
                    bot.data.logM.pop(guild.id)
                    return
                emb = await bot.as_embed(message, link=True)
                emb.colour = discord.Colour(0x00FF00)
                action = f"**모방 호출** {channel_mention(channel.id)}:\n"
                emb.description = lim_str(action + emb.description, 4096)
                emb.timestamp = message.created_at
                self.bot.send_embeds(c, emb)
            for mimic in m:
                await bot.data.mimics.update_mimic(mimic, guild)
                name = mimic.name
                url = mimic.url
                await wait_on_none(bot.send_as_webhook(channel, msg, username=name, avatar_url=url, tts=tts))
                mimic.count += 1
                mimic.total += len(msg)
            create_task(message.add_reaction("👀"))


class UpdateMimics(Database):
    name = "mimics"

    async def _nocommand_(self, message, **void):
        if not message.content:
            return
        user = message.author
        if user.id in self.data:
            bot = self.bot
            perm = bot.get_perms(user.id, message.guild)
            if perm < 1:
                return
            admin = not inf > perm
            if message.guild is not None:
                try:
                    enabled = bot.data.enabled[message.channel.id]
                except KeyError:
                    enabled = ()
            else:
                enabled = list(bot.categories)
            # User must have permission to use ~mimicsend in order to invoke by prefix
            if admin or "webhook" in enabled:
                database = self.data[user.id]
                msg = message.content
                with bot.ExceptionSender(message.channel, Exception, reference=message):
                    # Stack multiple messages to send, may be separated by newlines
                    sending = alist()
                    channel = message.channel
                    for line in msg.splitlines():
                        found = False
                        # O(1) time complexity per line regardless of how many mimics a user is assigned
                        if len(line) > 2 and " " in line:
                            i = line.index(" ")
                            prefix = line[:i]
                            if prefix in database:
                                mimics = database[prefix]
                                if mimics:
                                    line = line[i + 1:].strip(" ")
                                    for m in mimics:
                                        sending.append(cdict(m_id=m, msg=line))
                                    found = True
                        if not sending:
                            break
                        if not found:
                            sending[-1].msg += "\n" + line
                    if sending:
                        guild = message.guild
                        create_task(bot.silent_delete(message))
                        if guild and "logM" in bot.data and guild.id in bot.data.logM:
                            c_id = bot.data.logM[guild.id]
                            try:
                                c = await self.bot.fetch_channel(c_id)
                            except (EOFError, discord.NotFound):
                                bot.data.logM.pop(guild.id)
                                return
                            emb = await self.bot.as_embed(message, link=True)
                            emb.colour = discord.Colour(0x00FF00)
                            action = f"**모방 호출** {channel_mention(channel.id)}:\n"
                            emb.description = lim_str(action + emb.description, 4096)
                            emb.timestamp = message.created_at
                            self.bot.send_embeds(c, emb)
                        for k in sending:
                            mimic = self.data[k.m_id]
                            await self.update_mimic(mimic, guild=guild)
                            name = mimic.name
                            url = mimic.url
                            msg = escape_roles(k.msg)
                            if msg.startswith("/tts "):
                                msg = msg[5:]
                                tts = True
                            else:
                                tts = False
                            await wait_on_none(bot.send_as_webhook(channel, msg, username=name, avatar_url=url, tts=tts))
                            mimic.count += 1
                            mimic.total += len(k.msg)
                            bot.data.users.add_xp(user, math.sqrt(len(msg)) * 2)

    async def update_mimic(self, mimic, guild=None, it=None):
        if mimic.setdefault("auto", None):
            bot = self.bot
            mim = 0
            try:
                mim = verify_id(mimic.auto)
                if guild is not None:
                    user = guild.get_member(mim)
                if user is None:
                    user = await bot.fetch_user(mim)
                if user is None:
                    raise LookupError
                mimic.name = user.display_name
                mimic.url = await bot.get_proxy_url(user)
            except (discord.NotFound, LookupError):
                try:
                    mimi = bot.get_mimic(mim)
                    if it is None:
                        it = {}
                    # If we find the same mimic twice, there is an infinite loop
                    elif mim in it:
                        raise RecursionError("무한 재귀 루프 감지됨.")
                    it[mim] = True
                    if not len(it) & 255:
                        await asyncio.sleep(0.2)
                    await self.update_mimic(mimi, guild=guild, it=it)
                    mimic.name = mimi.name
                    mimic.url = mimi.url
                except LookupError:
                    mimic.name = str(mimic.auto)
                    mimic.url = "https://cdn.discordapp.com/embed/avatars/0.png"
        return mimic

    async def __call__(self):
        with tracebacksuppressor(SemaphoreOverflowError):
            async with self._semaphore:
                async with Delay(120):
                    # Garbage collector for unassigned mimics
                    i = 1
                    for m_id in tuple(self.data):
                        if type(m_id) is str:
                            mimic = self.data[m_id]
                            try:
                                if mimic.u_id not in self.data or mimic.id not in self.data[mimic.u_id][mimic.prefix]:
                                    self.data.pop(m_id)
                            except:
                                self.data.pop(m_id)
                        if not i % 8191:
                            await asyncio.sleep(0.45)
                        i += 1


class UpdateWebhooks(Database):
    name = "webhooks"
    channel = True
    CID = collections.namedtuple("id", ["id"])
    temp = {}

    def from_dict(self, d, c_id):
        d = copy.copy(d)
        d.url = f"https://discord.com/api/webhooks/{d.id}/{d.token}"
        w = discord.Webhook.from_url(d.url, session=self.bot._connection.http._HTTPClient__session, bot_token=self.bot.token)
        d.send = w.send
        d.edit = w.edit
        d.display_avatar = d.avatar_url = d.avatar and f"https://cdn.discordapp.com/avatars/{d.id}/{d.avatar}.png?size=1024"
        d.channel = self.CID(id=c_id)
        d.created_at = snowflake_time_3(w.id)
        return self.add(d)

    def to_dict(self, user):
        return cdict(
            id=user.id,
            name=user.name,
            avatar=getattr(user, "avatar_url", as_str(user.avatar)),
            token=user.token,
            owner_id=getattr(user, "owner_id", None) or user.user.id,
        )

    def add(self, w):
        user = self.bot.GhostUser()
        with suppress(AttributeError):
            user.channel = w.channel
        user.id = w.id
        user.name = w.name
        user.display_name = w.name
        user.joined_at = w.created_at
        user.avatar = w.avatar and (w.avatar if isinstance(w.avatar, str) else w.avatar.key)
        user.display_avatar = user.avatar_url = str(w.avatar)
        user.bot = True
        user.send = w.send
        user.edit = w.edit
        user.dm_channel = getattr(w, "channel", None)
        user.webhook = w
        try:
            user.user = w.user
        except AttributeError:
            user.user = w.user = self.bot.get_user(w.owner_id, replace=True)
        user.owner_id = w.user.id
        try:
            w.owner_id = w.user.id
        except AttributeError:
            pass
        try:
            sem = self.bot.cache.users[w.id].semaphore
        except (AttributeError, KeyError):
            sem = None
        self.bot.cache.users[w.id] = user
        if w.token:
            webhooks = self.data.setdefault(w.channel.id, cdict())
            webhooks[w.id] = self.to_dict(w)
            if sem is None:
                sem = Semaphore(5, 256, rate_limit=5)
            user.semaphore = sem
        return user

    async def get(self, channel, force=False, bypass=False):
        guild = getattr(channel, "guild", None)
        if not guild:
            raise TypeError("DM 채널은 웹후크를 가질 수 없습니다.")
        if not force:
            with suppress(KeyError):
                temp = self.temp[channel.id]
                if temp:
                    return temp
            if channel.id in self.data:
                self.temp[channel.id] = temp = alist(self.from_dict(w, channel.id) for w in self.data[channel.id].values() if (getattr(w, "user", None) or getattr(w, "owner_id", None)))
                if temp:
                    bot = True
                    for w in temp:
                        user = getattr(w, "user", None) or await self.bot.fetch_user(w.owner_id)
                        w.user = user
                        if not user.bot:
                            bot = False
                    if not bot:
                        for w in temp:
                            if w.user.bot:
                                await w.delete()
                                self.bot.cache.users.pop(w.id, None)
                        return [w for w in temp if not w.user.bot]
                    return temp
        async with self.bot.guild_semaphore if not bypass else emptyctx:
            self.data.pop(channel.id, None)
            if not channel.permissions_for(channel.guild.me).manage_webhooks:
                raise PermissionError("채널에서 웹후크를 만들 수 없습니다.")
            webhooks = None
            if guild.me.guild_permissions.manage_webhooks:
                with suppress(discord.Forbidden):
                    webhooks = await guild.webhooks()
            if webhooks is None:
                webhooks = await aretry(channel.webhooks, attempts=5, delay=15, exc=(discord.Forbidden, discord.NotFound))
        temp = [w for w in webhooks if (getattr(w, "user", None) or getattr(w, "owner_id", None)) and w.token and w.channel.id == channel.id]
        bot = True
        for w in temp:
            user = getattr(w, "user", None) or await self.bot.fetch_user(w.owner_id)
            w.user = user
            if not user.bot:
                bot = False
        if not bot:
            for w in temp:
                if w.user.bot:
                    await w.delete()
                    self.bot.cache.users.pop(w.id, None)
            return [w for w in temp if not w.user.bot]
        return temp
        self.temp[channel.id] = temp = alist(self.add(w) for w in temp)
        return temp