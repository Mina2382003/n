"""Dialogue for "بابا يسوع وتهدئة العاصفة" (Egyptian Arabic script, Mark 4:35-41).

Synthesises every line with Piper voices (each character has its own voice / pitch, everyone speaks slowly),
measures each line's loudness envelope to drive that character's mouth, and lays the film out:
  voices/dialogue.wav   all speech, mixed
  timeline.json         shots (which still, how long, camera keys, who talks when) for render.py / soundtrack.py

usage: python3 voices.py <dir with piper voice folders>
"""
import os, sys, json, glob, subprocess, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
XF = .8  # picture dissolve (s)

# ---- voices: piper model, pitch factor, formants ("shifted" = smaller vocal tract, i.e. a child), speed, gain
# (length_scale 1.0 = the voice's natural pace)
VOICES = {
    "narrator": dict(model="ar_JO-kareem-medium", pitch=.84, formant="preserved", slow=1.0, gain=1.0, warm=True),
    "jesus":    dict(model="ar_JO-kareem-medium", pitch=.95, formant="preserved", slow=1.05, gain=1.0, warm=True),
    "boy":      dict(model="ar_JO-kareem-medium", pitch=1.5, formant="shifted", slow=.95, gain=.95),
    "kid2":     dict(model="ar_JO-kareem-medium", pitch=1.6, formant="shifted", slow=.95, gain=.9),
    "girl":     dict(model="ar_JO-kareem-medium", pitch=1.7, formant="shifted", slow=.95, gain=.9),
    "d1":       dict(model="ar_JO-kareem-medium", pitch=.9, formant="preserved", slow=.97, gain=1.0),
    "d2":       dict(model="ar_JO-kareem-medium", pitch=1.02, formant="preserved", slow=.97, gain=1.0),
    "d3":       dict(model="ar_JO-kareem-medium", pitch=1.12, formant="preserved", slow=.97, gain=1.0),
    "man":      dict(model="ar_JO-kareem-medium", pitch=.86, formant="preserved", slow=1.0, gain=.8),
    "woman":    dict(model="ar_JO-kareem-medium", pitch=1.35, formant="shifted", slow=1.0, gain=.8),
}

# ---- the film: shots in story order. Each line: (voice(s), face seed(s) whose mouth moves, text, pronunciation)
# The only voices reachable here are trained on Levantine/standard Arabic, so every line is given as Egyptian
# (Cairene) pronunciation in IPA and spoken by the clearest one (kareem), reshaped per character:
# ج = ɡ, ق = ʔ, ث = s/t, ذ = z/d, colloquial vowels and stress. face seeds refer to rigs.RIGS (None = off screen).
KIDS = (("boy", 11), ("kid2", 12), ("girl", 13))
SHOTS = [
    dict(image=0, lines=[  # المشهد الأول: مقدمة القصة
        ("narrator", None, "البحر جميل وهادي، وفيه سمك ومراكب.",
         "ʔilbˈaħr ɡamˈiːl wihˈaːdi, wifˈiːh sˈamak wimarˈaːkib."),
        ("boy", 11, "مين يا ولاد بيحب يروح البحر؟", "mˈiːn ja wlˈaːd biħˈibb jirˈuːħ ilbˈaħr?"),
        ("kid2", 12, "أنااا!", "ʔanˈaːːː!"),
        ("boy", 11, "والبحر فيه إيه؟", "wilbˈaħr fˈiːh ʔˈiːh?"),
        (KIDS, None, "سمك!", "samˈaːk!"),
        ("boy", 11, "وفيه حاجة بتمشي في البحر، يا ترى إيه؟", "wifˈiːh ħˈaːɡa bitˈimʃi filbˈaħr, ja tˈara ʔˈiːh?"),
        (KIDS, None, "مراكب!", "maraːkˈiːb!"),
        ("boy", 11, "طب هحكيلكم قصة عن مركب في البحر!", "tˤˈab ħaħkilˈkum ʔˈisˤsˤa ʕan mˈarkib filbˈaħr!"),
    ]),
    dict(image=1, lines=[  # المشهد الثاني: بابا يسوع بيعلم الشعب
        ("narrator", None, "مرة زمان، أيام بابا يسوع، كان فيه ناس كتير قاعدين يسمعوا بابا يسوع طول النهار.",
         "mˈarra zamˈaːn, ʔajjˈaːm bˈaːba jasˈuːʕ, kˈaːn fˈiːh nˈaːs kitˈiːr ʔaʕdˈiːn jisˈmaʕu bˈaːba jasˈuːʕ tˤuːl innahˈaːr."),
        ("jesus", 21, "ربنا بيحبكم كلكم، وعايزكم تحبوا بعض، وتساعدوا بعض.",
         "rabbˈina biħibbˈukum kullˈukum, wiʕajzˈinkum tiħˈibbu bˈaʕd, witsaʕdu bˈaʕd."),
        ((("man", 25), ("woman", 26), ("girl", 22), ("kid2", 24), ("d3", 23)), None, "إحنا بنحب نسمع كلامك يا يسوع!",
         "ʔˈiħna binħˈibb nˈismaʕ kalˈaːmak ja jasˈuːʕ!"),
        ("narrator", None, "وبعد يوم طويل، بابا يسوع تعب.", "wibˈaʕd jˈoːm tˤawˈiːl, bˈaːba jasˈuːʕ tˈiʕib."),
    ]),
    dict(image=2, lines=[
        ("jesus", 31, "يلا بينا نعدّي الناحية التانية.", "jˈalla bˈiːna nʕˈaddi innˈaħja ittˈanja."),
    ]),
    dict(image=3, lines=[  # المشهد الثالث: المركب والبحر الهادي
        ("narrator", None, "بابا يسوع والتلاميذ ركبوا المركب، والبحر هادي وجميل.",
         "bˈaːba jasˈuːʕ wittalamˈiːz rˈikbu ilmˈarkib, wilbˈaħr hˈaːdi wiɡamˈiːl."),
        ("d1", 44, "ياااه! البحر جميل أوي النهارده!", "jˈaːːh! ʔilbˈaħr ɡamˈiːl ʔˈawi innahˈarda!"),
        ("d2", 42, "والموج هادي خالص!", "wilmˈoːɡ hˈaːdi xˈaːlisˤ!"),
    ]),
    dict(image=4, lines=[
        ("narrator", None, "وبابا يسوع كان تعبان، فراح نام على مخدة صغيرة في المركب.",
         "wibˈaːba jasˈuːʕ kˈaːn taʕbˈaːn, faraːħ nˈaːm ʕˈala maxˈadda sˤuɣajjˈara filmˈarkib."),
    ]),
    dict(image=5, lines=[  # المشهد الرابع: العاصفة
        ("narrator", None, "فجأة السما تتغير، والهوا يزيد، والمطر ينزل، والموج يعلى.",
         "fˈaɡʔa issˈama titɣˈajjar, wilhˈawa jizˈiːd, wilmˈatˤar jinˈzil, wilmˈoːɡ jˈiʕla."),
        ("d1", 61, "إيه ده؟! الهوا بقى شديد!", "ʔˈiːh dˈa?! ʔilhˈawa bˈaʔa ʃadˈiːd!"),
        ("d2", 63, "والموج بيعلى أوي!", "wilmˈoːɡ bijˈiʕla ʔˈawi!"),
        ("d3", 62, "الحقوا! الميه بدأت تدخل المركب!", "ʔilħˈaʔu! ʔilmˈajja badˈaʔit tˈudxul ilmˈarkib!"),
        ("narrator", None, "التلاميذ خافوا جدا، وكانوا ماسكين في المركب جامد، ومش عارفين يوصلوا لبابا يسوع علشان يصحّوه.",
         "ʔittalamˈiːz xˈaːfu ɡˈiddan, wikˈaːnu maskˈiːn filmˈarkib ɡˈaːmid, wimˈiʃ ʕarfˈiːn jiwsˈalu libˈaːba jasˈuːʕ ʕalaʃˈaːn jisˤaħˈħuːh."),
    ]),
    dict(image=6, lines=[  # المشهد الخامس: التلاميذ بيصحّوا بابا يسوع
        ("d1", 71, "امسكوا كويس! لازم نصحّي بابا يسوع!", "ʔimsˈiku kwˈajjis! lˈaːzim nisˤˈaħħi bˈaːba jasˈuːʕ!"),
        ("d2", 72, "يا بابا يسوع! اصحى!", "ja bˈaːba jasˈuːʕ! ʔˈisˤħa!"),
        ((("d1", 71), ("d2", 72), ("d3", 74), ("man", 73)), None, "يا بابا يسوع! الحقنا! هنغرق!",
         "ja bˈaːba jasˈuːʕ! ʔilħaʔˈna! haniɣrˈaʔ!"),
    ]),
    dict(image=7, lines=[  # المشهد السادس: بابا يسوع بيهدي العاصفة
        ("jesus", 81, "اسكت! ابكم!", "ʔuskˈut! ʔibkˈam!"),
    ], arm_line=0),
    dict(image=8, xf=2.0, calm=True, lines=[  # the storm dissolves into the calm sunset on this line
        ("narrator", None, "فجأة الرياح تسكت، والموج يهدا، والمطر يقف، والبحر يرجع هادي وجميل.",
         "fˈaɡʔa irrijˈaːħ tiskˈut, wilmˈoːɡ jˈihda, wilmˈatˤar jˈuʔaf, wilbˈaħr jˈirɡaʕ hˈaːdi wiɡamˈiːl."),
        ("d1", 92, "ياااه! البحر هدي!", "jˈaːːh! ʔilbˈaħr hˈidi!"),
        ("d2", 94, "والموج وقف خالص!", "wilmˈoːɡ wˈiʔif xˈaːlisˤ!"),
        ("d3", 97, "إزاي الرياح والبحر بيسمعوا كلام بابا يسوع؟!", "ʔizzˈaːj irrijˈaːħ wilbˈaħr bjisˈmaʕu kalˈaːm bˈaːba jasˈuːʕ?!"),
        ("jesus", 91, "إنتوا خايفين ليه؟ إزاي ما عندكوش إيمان؟", "ʔˈintu xajfˈiːn lˈiːh? ʔizzˈaːj ma ʕandˈukuːʃ ʔiːmˈaːn?"),  # المشهد السابع
        ("narrator", None, "التلاميذ عرفوا إن بابا يسوع له سلطان، حتى على الرياح والبحر.",
         "ʔittalamˈiːz ʕˈirfu ʔinn bˈaːba jasˈuːʕ lˈiːh sultˤˈaːn, ħˈatta ʕˈala rrijˈaːħ wilbˈaħr."),
    ]),
    dict(image=0, lines=[  # المشهد الثامن: نهاية القصة
        ("boy", 11, "وأنا كمان، لما أخاف، هصلّي لبابا يسوع، وأثق إنه سامعني ومعايا.",
         "wiʔˈana kamˈaːn, lˈamma ʔaxˈaːf, hasˤˈalli libˈaːba jasˈuːʕ, wˈasiʔ ʔˈinnu samʕˈiːni wimʕˈaːja."),
        (KIDS, None, "إحنا بنحبك يا بابا يسوع!", "ʔˈiħna binħˈibbak ja bˈaːba jasˈuːʕ!"),
    ]),
    dict(image=8, card=True, lines=[
        ("narrator", None, "لما أخاف، هثق في بابا يسوع.", "lˈamma ʔaxˈaːf, hˈasiʔ fi bˈaːba jasˈuːʕ."),
    ]),
]

GAP = .3       # breath between lines
PRE, POST = .8, .7


def synth(voices_dir, vname, text, ipa=None):
    from piper import PiperVoice, SynthesisConfig
    v = VOICES[vname]
    if not hasattr(synth, "cache"):
        synth.cache = {}
    if v["model"] not in synth.cache:
        m = glob.glob(f"{voices_dir}/vits-piper-{v['model']}/*.onnx")[0]
        synth.cache[v["model"]] = PiperVoice.load(m)
    pv = synth.cache[v["model"]]
    ch = list(pv.synthesize(f"[[{ipa}]]" if ipa else text, syn_config=SynthesisConfig(length_scale=v["slow"], noise_scale=.6, noise_w_scale=.7)))
    x = np.concatenate([c.audio_float_array for c in ch]).astype(np.float32)
    sr = ch[0].sample_rate
    with tempfile.TemporaryDirectory() as td:
        import wave
        a, b = f"{td}/a.wav", f"{td}/b.wav"
        with wave.open(a, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
        af = [f"rubberband=pitch={v['pitch']}:formant={v['formant']}:pitchq=quality" if v["pitch"] != 1 else "anull",
              f"aresample={SR}", "highpass=f=70", "afade=t=in:d=0.02"]
        if v.get("warm"):
            af += ["equalizer=f=180:t=q:w=1:g=2", "aecho=0.8:0.6:45|70:0.12|0.08"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", ",".join(af), "-ac", "1", b], check=True)
        with wave.open(b) as w:
            y = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    # trim silence at the ends
    e = np.convolve(np.abs(y), np.ones(441) / 441, "same")
    idx = np.where(e > .004)[0]
    if len(idx):
        y = y[max(0, idx[0] - 1500): idx[-1] + 4000]
    y = y / (np.abs(y).max() + 1e-6) * .8 * v["gain"]
    return y


def envelope(y):
    """mouth opening 0..1 at 100 Hz from the line's loudness"""
    hop = SR // 100
    n = len(y) // hop + 1
    r = np.array([np.sqrt((y[i * hop:(i + 1) * hop] ** 2).mean() + 1e-12) for i in range(n)])
    r = np.convolve(r, np.ones(3) / 3, "same")
    r = r / (np.percentile(r, 92) + 1e-6)
    return np.clip((r - .12) / .88, 0, 1) ** .8


def main(voices_dir):
    sys.path.insert(0, HERE)
    import rigs
    os.makedirs(f"{HERE}/voices", exist_ok=True)
    shots, mix, t_global = [], [], 0.0
    report = []
    for si, sh in enumerate(SHOTS):
        if si:  # this shot fades in over the previous one
            t_global -= sh.get("xf", XF)
        t = max(PRE, sh.get("xf", XF) + .2)
        talk, keys, line_times = {}, [], []
        for li, (who, face, text, ipa) in enumerate(sh["lines"]):
            parts = who if isinstance(who, tuple) else ((who, face),)
            tracks = []
            for k, (vn, fs) in enumerate(parts):
                y = synth(voices_dir, vn, text, ipa)
                if len(parts) > 1:  # a chorus: the first voice leads, the others a little behind and softer
                    y = np.concatenate([np.zeros(int(SR * .025 * k), np.float32), y]) * (.8 if k == 0 else .45)
                tracks.append((vn, fs, y))
            n = max(len(y) for _, _, y in tracks)
            line = np.zeros(n, np.float32)
            for vn, fs, y in tracks:
                line[:len(y)] += y
                if fs is not None:
                    talk.setdefault(str(fs), []).append([round(t, 3), np.round(envelope(y), 3).tolist()])
            dur = n / SR
            mix.append((t_global + t, line))
            speaker = [fs for _, fs, _ in tracks if fs is not None]
            keys.append(dict(t=round(t, 3), faces=speaker, narrator=all(vn == "narrator" for vn, _, _ in tracks)))
            line_times.append((t, dur))
            report.append((si, li, parts[0][0], text, dur, line))
            t += dur + GAP
        dur = t - GAP + POST
        shot = dict(image=sh["image"], start=round(t_global, 3), d=round(dur, 3), talk=talk, keys=keys,
                    card=sh.get("card", False), xf=sh.get("xf", XF), calm=sh.get("calm", False),
                    lines=[[round(a, 3), round(b, 3)] for a, b in line_times])
        if "arm_line" in sh:
            shot["limb_t0"] = round(line_times[sh["arm_line"]][0] - 1.0, 3)
        shots.append(shot)
        t_global += dur
    total = shots[-1]["start"] + shots[-1]["d"]
    out = np.zeros(int(total * SR) + SR, np.float32)
    for t0, y in mix:
        i = int(t0 * SR)
        out[i:i + len(y)] += y
    out = out / (np.abs(out).max() + 1e-6) * .9
    import wave
    with wave.open(f"{HERE}/voices/dialogue.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())
    json.dump(dict(xf=XF, total=round(total, 3), shots=shots), open(f"{HERE}/timeline.json", "w"))
    print(f"total {total:.1f}s, {len(shots)} shots")
    return report


if __name__ == "__main__":
    rep = main(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == "check":  # transcribe every line back with Whisper
        import sherpa_onnx
        w = f"{sys.argv[1]}/sherpa-onnx-whisper-small"
        r = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=w + "/small-encoder.int8.onnx", decoder=w + "/small-decoder.int8.onnx",
                                                        tokens=w + "/small-tokens.txt", language="ar", task="transcribe", num_threads=4)
        for si, li, vn, text, dur, y in rep:
            y = np.concatenate([np.zeros(SR // 2, np.float32), y, np.zeros(SR, np.float32)])  # whisper drops clip edges
            s = r.create_stream(); s.accept_waveform(SR, y); r.decode_stream(s)
            print(f"{si}.{li} {vn:8s} {dur:4.1f}s | {text} | -> {s.result.text}")
