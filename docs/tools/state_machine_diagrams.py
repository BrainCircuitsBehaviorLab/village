# ruff: noqa: C408, E501 -- specs read better as dict(...); long labels
"""Draws the state machine diagram of each example Bpod task (one PNG per task).

The diagrams are drawn by hand from each task's create_trial: every task has a
spec in SPECS below (states with their timer and outputs, transitions with the
event that causes them, notes). After changing an example task, update its spec
and run, from the repository root:

    python docs/tools/state_machine_diagrams.py

The PNGs are written to docs/source/_static/examples/.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

INK = "#1f2937"
MUTED = "#6b7280"
KINDS = {
    "state": ("#e8f0fe", "#3b6fd8", "-"),
    "reward": ("#e6f4ea", "#2f9e44", "-"),
    "penalty": ("#fdecea", "#d9480f", "-"),
    "exit": ("#f3f4f6", INK, "--"),
}
SCALE = 0.72  # inches per data unit
NAME_FS, LINE_FS, EDGE_FS = 12, 9.5, 9.5


def box_size(name, lines):
    w = max(0.15 * len(name) + 0.7, max([0.092 * len(s) + 0.45 for s in lines] + [0]))
    h = 0.75 + 0.33 * len(lines)
    return w, h


def draw(spec, path):
    W, H = spec["size"]
    fig = plt.figure(figsize=(W * SCALE, H * SCALE), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.set_aspect("equal")
    ax.axis("off")

    patches, centers = {}, {}
    for key, node in spec["nodes"].items():
        x, y = node["xy"]
        y += spec.get("yshift", 0)
        centers[key] = (x, y)
        kind = node.get("kind", "state")
        if kind == "start":
            p = Circle((x, y), 0.18, color=INK)
            ax.add_patch(p)
            patches[key] = p
            continue
        name = node.get("label", key)
        lines = node.get("lines", [])
        w, h = box_size(name, lines)
        w = node.get("w", w)
        fc, ec, ls = KINDS[kind]
        p = FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0.02,rounding_size=0.16",
            fc=fc,
            ec=ec,
            lw=1.7,
            ls=ls,
        )
        ax.add_patch(p)
        patches[key] = p
        if lines:
            ax.text(
                x,
                y + h / 2 - 0.36,
                name,
                ha="center",
                va="center",
                fontsize=NAME_FS,
                fontweight="bold",
                color=INK,
            )
            ax.plot(
                [x - w / 2 + 0.15, x + w / 2 - 0.15],
                [y + h / 2 - 0.66] * 2,
                color=ec,
                lw=0.7,
            )
            ax.text(
                x,
                y + h / 2 - 0.72 - 0.165 * len(lines),
                "\n".join(lines),
                ha="center",
                va="center",
                fontsize=LINE_FS,
                color=INK,
                linespacing=1.45,
            )
        else:
            ax.text(
                x,
                y,
                name,
                ha="center",
                va="center",
                fontsize=NAME_FS,
                fontweight="bold",
                color=INK,
            )
        if node.get("note"):
            ax.text(
                x,
                y - h / 2 - 0.12,
                node["note"],
                ha="center",
                va="top",
                fontsize=8.5,
                color=MUTED,
                style="italic",
            )

    for edge in spec["edges"]:
        src, dst, label = edge[:3]
        opt = edge[3] if len(edge) > 3 else {}
        rad = opt.get("rad", 0.0)
        ax.annotate(
            "",
            xy=centers[dst],
            xytext=centers[src],
            arrowprops=dict(
                arrowstyle="-|>",
                color=INK,
                lw=1.5,
                mutation_scale=15,
                connectionstyle=f"arc3,rad={rad}",
                patchA=patches[src],
                patchB=patches[dst],
                shrinkA=2,
                shrinkB=2,
            ),
        )
        if label:
            (x0, y0), (x2, y2) = centers[src], centers[dst]
            dx, dy = x2 - x0, y2 - y0
            t = opt.get("t", 0.5)
            lx = x0 + t * dx + 0.5 * rad * dy + opt.get("dx", 0)
            ly = y0 + t * dy - 0.5 * rad * dx + opt.get("dy", 0)
            ax.text(
                lx,
                ly,
                label,
                ha=opt.get("ha", "center"),
                va=opt.get("va", "center"),
                fontsize=EDGE_FS,
                color=INK,
                linespacing=1.3,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none"),
            )

    ax.text(
        0.3, H - 0.3, spec["title"], fontsize=15, fontweight="bold", color=INK, va="top"
    )
    if spec.get("subtitle"):
        ax.text(0.3, H - 0.85, spec["subtitle"], fontsize=10, color=MUTED, va="top")
    y = 0.3 + 0.36 * (len(spec.get("footer", [])) - 1)
    for line in spec.get("footer", []):
        ax.text(0.3, y, line, fontsize=9.5, color=MUTED, va="bottom")
        y -= 0.36
    fig.savefig(path, facecolor="white")
    plt.close(fig)


SIDE_NOTE = (
    "side = random every trial:  left → Port1In · LED PWM1 · Valve1      "
    "right → Port3In · LED PWM3 · Valve3"
)

SPECS = {}

# --------------------------------------------------------------- 1 habituation
SPECS["bpod_1_habituation"] = dict(
    size=(13, 5.4),
    yshift=-0.6,
    title="Bpod1Habituation — state machine (one trial)",
    subtitle="Habituation: nothing happens, port pokes are only registered.",
    nodes={
        "start": dict(kind="start", xy=(0.7, 3.4)),
        "ready_to_explore": dict(xy=(3.9, 3.4), lines=["timer: 60 s", "out: none"]),
        "exit": dict(kind="exit", xy=(11.3, 3.4), note="end of trial → after_trial()"),
    },
    edges=[
        ("start", "ready_to_explore", ""),
        (
            "ready_to_explore",
            "exit",
            "Tup (60 s)\nPort1In\nPort2In\nPort3In\n" "(any of these)",
            dict(),
        ),
    ],
    footer=[
        "after_trial(): outcome = miss / left_poke (Port1) / center_poke (Port2) / "
        "right_poke (Port3);  water = 0",
    ],
)

# ----------------------------------------------------------------- 2 passive
SPECS["bpod_2_passive"] = dict(
    size=(16, 7.0),
    yshift=0.4,
    title="Bpod2Passive — state machine (one trial)",
    subtitle="Passive learning: the water is already delivered when the LED turns on.",
    nodes={
        "start": dict(kind="start", xy=(0.7, 3.6)),
        "water_delivery": dict(
            xy=(3.5, 3.6),
            lines=["timer: valve time (reward_volume)", "out: side LED + side valve"],
            kind="reward",
        ),
        "led_on": dict(xy=(8.0, 3.6), lines=["timer: led_on_time", "out: side LED"]),
        "iti": dict(xy=(12.0, 3.6), lines=["timer: iti_time", "out: none"]),
        "exit": dict(kind="exit", xy=(15.0, 3.6)),
        "exit2": dict(kind="exit", label="exit", xy=(8.0, 1.75)),
    },
    edges=[
        ("start", "water_delivery", ""),
        ("water_delivery", "led_on", "Tup", dict(dy=0.3)),
        ("led_on", "iti", "correct-side\npoke", dict(dy=0.5)),
        ("iti", "exit", "Tup", dict(dy=0.3)),
        ("led_on", "exit2", "Tup (no poke)", dict(dx=0.95)),
    ],
    footer=[
        SIDE_NOTE,
        "A wrong-side poke does not change state (it is only logged).",
        "after_trial(): first poke after the LED → outcome correct / incorrect / "
        "miss;  water = reward_volume (always)",
    ],
)

# ------------------------------------------------------------------ 3 active
SPECS["bpod_3_active"] = dict(
    size=(16, 7.0),
    yshift=0.4,
    title="Bpod3Active — state machine (one trial)",
    subtitle="Active learning: the water comes only after poking the lit port.",
    nodes={
        "start": dict(kind="start", xy=(0.7, 3.6)),
        "led_on": dict(xy=(3.3, 3.6), lines=["timer: led_on_time", "out: side LED"]),
        "water_delivery": dict(
            xy=(8.0, 3.6),
            lines=[
                "timer: valve time",
                "(reward_volume, 10%: large)",
                "out: side valve + side LED",
            ],
            kind="reward",
        ),
        "iti": dict(xy=(12.0, 3.6), lines=["timer: iti_time", "out: none"]),
        "exit": dict(kind="exit", xy=(15.0, 3.6)),
        "exit2": dict(kind="exit", label="exit", xy=(3.3, 1.75)),
    },
    edges=[
        ("start", "led_on", ""),
        ("led_on", "water_delivery", "correct-side\npoke", dict(dy=0.5)),
        ("water_delivery", "iti", "Tup", dict(dy=0.3)),
        ("iti", "exit", "Tup", dict(dy=0.3)),
        ("led_on", "exit2", "Tup (no poke)", dict(dx=0.95)),
    ],
    footer=[
        SIDE_NOTE,
        "A wrong-side poke does not change state (it is only logged).",
        "after_trial(): first poke after the LED → outcome correct / incorrect / "
        "miss;  water only if correct",
    ],
)

# ------------------------------------------------------- 4 center initiated
SPECS["bpod_4_center_initiated"] = dict(
    size=(20, 7.2),
    yshift=0.4,
    title="Bpod4CenterInitiated — state machine (one trial)",
    subtitle="The animal starts the trial by poking the center port.",
    nodes={
        "start": dict(kind="start", xy=(0.7, 3.8)),
        "c_led_on": dict(
            xy=(3.4, 3.8), lines=["timer: c_led_on_time", "out: center LED (PWM2)"]
        ),
        "side_led_on": dict(
            xy=(7.9, 3.8), lines=["timer: led_on_time", "out: side LED"]
        ),
        "water_delivery": dict(
            xy=(12.6, 3.8),
            lines=[
                "timer: valve time",
                "(reward_volume, 10%: large)",
                "out: side valve",
            ],
            kind="reward",
        ),
        "iti": dict(xy=(16.4, 3.8), lines=["timer: iti_time", "out: none"]),
        "exit": dict(kind="exit", xy=(19.0, 3.8)),
        "exit_c": dict(kind="exit", label="exit", xy=(3.4, 1.85)),
        "exit_s": dict(kind="exit", label="exit", xy=(7.9, 1.85)),
    },
    edges=[
        ("start", "c_led_on", ""),
        ("c_led_on", "side_led_on", "Port2In", dict(dy=0.3)),
        ("side_led_on", "water_delivery", "correct-side\npoke", dict(dy=0.5)),
        ("water_delivery", "iti", "Tup", dict(dy=0.3)),
        ("iti", "exit", "Tup", dict(dy=0.3)),
        ("c_led_on", "exit_c", "Tup", dict(dx=0.4)),
        ("side_led_on", "exit_s", "Tup", dict(dx=0.4)),
    ],
    footer=[
        SIDE_NOTE,
        "A wrong-side poke does not change state (it is only logged).",
        "after_trial(): no center poke → omission;  first side poke → correct / "
        "incorrect;  none → miss;  water only if correct",
    ],
)

# ------------------------------------------------------ 5 introduce penalty
SPECS["bpod_5_introduce_penalty"] = dict(
    size=(20.5, 9.2),
    title="Bpod5IntroducePenalty — state machine (one trial)",
    subtitle="Like Bpod4, but a wrong-side poke now gives a sound and a time-out.",
    nodes={
        "start": dict(kind="start", xy=(0.7, 5.6)),
        "c_led_on": dict(
            xy=(3.5, 5.6),
            lines=[
                "timer: c_led_on_time",
                "out: center LED (PWM2)",
                "+ SoftCode2 (load penalty sound)",
            ],
        ),
        "side_led_on": dict(
            xy=(8.5, 5.6), lines=["timer: led_on_time", "out: side LED"]
        ),
        "water_delivery": dict(
            xy=(13.0, 5.6),
            lines=[
                "timer: valve time",
                "(reward_volume, 10%: large)",
                "out: side valve",
            ],
            kind="reward",
        ),
        "iti": dict(xy=(16.9, 5.6), lines=["timer: iti_time", "out: none"]),
        "exit": dict(kind="exit", xy=(19.5, 5.6)),
        "exit_c": dict(kind="exit", label="exit", xy=(3.5, 3.0)),
        "exit_s": dict(kind="exit", label="exit", xy=(8.5, 7.9)),
        "wrong_choice": dict(
            xy=(8.5, 2.7),
            lines=["timer: noise_time", "out: SoftCode4 (play penalty sound)"],
            kind="penalty",
        ),
        "timeout": dict(
            xy=(13.4, 2.7),
            lines=["timer: timeout − noise_time", "out: none"],
            kind="penalty",
        ),
        "exit_p": dict(kind="exit", label="exit", xy=(17.2, 2.7)),
    },
    edges=[
        ("start", "c_led_on", ""),
        ("c_led_on", "side_led_on", "Port2In", dict(dy=0.3)),
        ("side_led_on", "water_delivery", "correct-side\npoke", dict(dy=0.5)),
        ("water_delivery", "iti", "Tup", dict(dy=0.3)),
        ("iti", "exit", "Tup", dict(dy=0.3)),
        ("c_led_on", "exit_c", "Tup", dict(dx=0.4)),
        ("side_led_on", "exit_s", "Tup", dict(dx=0.4)),
        ("side_led_on", "wrong_choice", "wrong-side\npoke", dict(dx=0.85)),
        ("wrong_choice", "timeout", "Tup", dict(dy=0.3)),
        ("timeout", "exit_p", "Tup", dict(dy=0.3)),
    ],
    footer=[
        SIDE_NOTE,
        "after_trial(): no center poke → omission;  first side poke → correct / "
        "incorrect;  none → miss;  water only if correct",
    ],
)

# ------------------------------------------------------------------- 6 delay
SPECS["bpod_6_delay"] = dict(
    size=(21, 11.2),
    title="Bpod6Delay — state machine (one trial)",
    subtitle="Poke the side that lit up first. The second side lights up after a "
    "random delay (harder when p is higher).",
    nodes={
        "start": dict(kind="start", xy=(0.7, 5.6)),
        "c_led_on": dict(
            xy=(3.4, 5.6),
            lines=[
                "timer: c_led_on_time",
                "out: center LED (PWM2)",
                "+ SoftCode2 (load penalty sound)",
            ],
        ),
        "first_side_led": dict(
            xy=(8.2, 5.6),
            lines=["timer: delay (random, from p)", "out: first-side LED"],
        ),
        "both_side_leds": dict(
            xy=(13.2, 5.6), lines=["timer: 40 s − delay", "out: both side LEDs"]
        ),
        "exit_n": dict(kind="exit", label="exit", xy=(18.6, 5.6), note="no response"),
        "correct_choice": dict(
            xy=(10.7, 8.9),
            lines=[
                "timer: valve time",
                "(reward_volume, 10%: large)",
                "out: correct-side valve",
            ],
            kind="reward",
        ),
        "iti": dict(xy=(15.2, 8.9), lines=["timer: iti_time", "out: none"]),
        "exit": dict(kind="exit", xy=(18.6, 8.9)),
        "wrong_choice": dict(
            xy=(10.7, 2.3),
            lines=["timer: noise_time", "out: SoftCode4 (play penalty sound)"],
            kind="penalty",
        ),
        "timeout": dict(
            xy=(15.6, 2.3),
            lines=["timer: timeout − noise_time", "out: none"],
            kind="penalty",
        ),
        "exit_p": dict(kind="exit", label="exit", xy=(19.4, 2.3)),
        "exit_c": dict(kind="exit", label="exit", xy=(3.4, 2.3), note="omission"),
    },
    edges=[
        ("start", "c_led_on", ""),
        ("c_led_on", "first_side_led", "Port2In", dict(dy=0.3)),
        ("c_led_on", "exit_c", "Tup (no center\npoke)", dict(dx=0.95)),
        ("first_side_led", "both_side_leds", "Tup", dict(dy=0.3)),
        ("both_side_leds", "exit_n", "Tup", dict(dy=0.3)),
        ("first_side_led", "correct_choice", "correct poke", dict(dx=-0.85)),
        ("both_side_leds", "correct_choice", "correct poke", dict(dx=0.85)),
        ("first_side_led", "wrong_choice", "wrong poke", dict(dx=-0.8)),
        ("both_side_leds", "wrong_choice", "wrong poke", dict(dx=0.8)),
        ("correct_choice", "iti", "Tup", dict(dy=0.3)),
        ("iti", "exit", "Tup", dict(dy=0.3)),
        ("wrong_choice", "timeout", "Tup", dict(dy=0.3)),
        ("timeout", "exit_p", "Tup", dict(dy=0.3)),
    ],
    footer=[
        "first side = left (Port1In · PWM1 · Valve1) or right (Port3In · PWM3 · "
        "Valve3), chosen at random every trial",
        "after_trial(): no center poke → omission (not used to adapt p);  first poke → "
        "correct / incorrect;  none → miss;  water only if correct",
    ],
)

# -------------------------------------------------------------- area2 sound
SPECS["bpod_area2_sound"] = dict(
    size=(14.5, 6.6),
    title="BpodArea2Sound — state machine (one trial)",
    subtitle="Driven by the box camera: entering area 2 gives a sound and water "
    "together.",
    nodes={
        "start": dict(kind="start", xy=(0.7, 3.6)),
        "wait_area2": dict(xy=(3.4, 3.6), lines=["timer: 60 s", "out: none"]),
        "deliver": dict(
            xy=(9.0, 3.6),
            lines=[
                "timer: valve time (reward_volume)",
                "out: SoftCode4 (play sound) + Valve1",
            ],
            kind="reward",
        ),
        "exit": dict(kind="exit", xy=(13.3, 3.6)),
        "exit2": dict(kind="exit", label="exit", xy=(3.4, 1.75)),
    },
    edges=[
        ("start", "wait_area2", ""),
        (
            "wait_area2",
            "deliver",
            "SoftCode1\n(camera_trigger:\nentered area 2)",
            dict(dy=0.75),
        ),
        ("deliver", "exit", "Tup", dict(dy=0.3)),
        ("wait_area2", "exit2", "Tup (no entry)", dict(dx=0.95)),
    ],
    footer=[
        "Needs CAM_BOX_TRACKING_POSITION ON and BOX area 2 set to TRIGGER.",
        "after_trial(): entered_area2 = True / False;  water = reward_volume if "
        "entered, else 0",
    ],
)

# ------------------------------------------------------- global timer demo
SPECS["bpod_example_global_timer"] = dict(
    size=(14.5, 7.4),
    title="BpodExampleGlobalTimer — state machine (one trial)",
    subtitle="Demo: a 10 s global timer bounds the whole trial; each poke in port 1 "
    "flashes LED1.",
    nodes={
        "start": dict(kind="start", xy=(0.7, 4.4)),
        "trigger_global_timer": dict(
            xy=(3.7, 4.4), lines=["timer: 0", "out: GlobalTimer1Trig"]
        ),
        "wait_poke_or_timer": dict(xy=(8.0, 4.4), lines=["timer: none", "out: none"]),
        "poked": dict(xy=(12.4, 4.4), lines=["timer: 0.1 s", "out: LED1 (PWM1 = 255)"]),
        "exit": dict(kind="exit", xy=(10.2, 1.7)),
    },
    edges=[
        ("start", "trigger_global_timer", ""),
        ("trigger_global_timer", "wait_poke_or_timer", "Tup", dict(dy=0.3)),
        ("wait_poke_or_timer", "poked", "Port1In", dict(rad=-0.35)),
        ("poked", "wait_poke_or_timer", "Tup", dict(rad=-0.35)),
        ("wait_poke_or_timer", "exit", "GlobalTimer1End", dict(dx=-0.95)),
        ("poked", "exit", "GlobalTimer1End", dict(dx=0.95)),
    ],
    footer=[
        "Before the states: set_global_timer(timer_id=1, timer_duration=10 s).",
        "after_trial(): pokes = number of times 'poked' was entered",
    ],
)

# -------------------------------------------------- outputs and events demo
SPECS["bpod_example_outputs_and_events"] = dict(
    size=(19.5, 13.4),
    yshift=0.8,
    title="BpodExampleOutputsAndEvents — state machine (one trial)",
    subtitle="Demo of the Bpod primitives, step by step (follow the arrows).",
    nodes={
        "start": dict(kind="start", xy=(0.7, 9.6)),
        "wait_port1": dict(xy=(3.0, 9.6), lines=["timer: none", "out: none"]),
        "led1_on": dict(xy=(7.4, 9.6), lines=["timer: none", "out: LED1 (PWM1 = 255)"]),
        "wait_port3": dict(xy=(11.8, 9.6), lines=["timer: none", "out: none"]),
        "led3_on": dict(
            xy=(16.2, 9.6), lines=["timer: none", "out: LED3 (PWM3 = 120)"]
        ),
        "wait_before_valve": dict(xy=(16.2, 6.3), lines=["timer: 1 s", "out: none"]),
        "valve_open": dict(
            xy=(11.8, 6.3), lines=["timer: 0.1 s", "out: Valve2"], kind="reward"
        ),
        "wait_before_softcode": dict(xy=(7.4, 6.3), lines=["timer: 1 s", "out: none"]),
        "send_softcode": dict(xy=(3.0, 6.3), lines=["timer: 0", "out: SoftCode1"]),
        "wait_before_ttl": dict(xy=(3.0, 3.0), lines=["timer: 1 s", "out: none"]),
        "send_ttl": dict(xy=(7.4, 3.0), lines=["timer: 0.5 s", "out: BNC1High"]),
        "wait_response": dict(xy=(11.8, 3.0), lines=["timer: 10 s", "out: none"]),
        "ttl": dict(xy=(15.9, 4.5), lines=["timer: 0"]),
        "softcode": dict(xy=(15.9, 1.6), lines=["timer: 0"]),
        "exit": dict(kind="exit", xy=(11.8, 0.85)),
        "exit_t": dict(kind="exit", label="exit", xy=(18.6, 3.05)),
    },
    edges=[
        ("start", "wait_port1", ""),
        ("wait_port1", "led1_on", "Port1In", dict(dy=0.3)),
        ("led1_on", "wait_port3", "Port1Out", dict(dy=0.3)),
        ("wait_port3", "led3_on", "Port3In", dict(dy=0.3)),
        ("led3_on", "wait_before_valve", "Port3Out", dict(dx=0.6)),
        ("wait_before_valve", "valve_open", "Tup", dict(dy=0.3)),
        ("valve_open", "wait_before_softcode", "Tup", dict(dy=0.3)),
        ("wait_before_softcode", "send_softcode", "Tup", dict(dy=0.3)),
        ("send_softcode", "wait_before_ttl", "Tup", dict(dx=0.35)),
        ("wait_before_ttl", "send_ttl", "Tup", dict(dy=0.3)),
        ("send_ttl", "wait_response", "Tup", dict(dy=0.3)),
        ("wait_response", "ttl", "BNC1High", dict(dy=0.35)),
        (
            "wait_response",
            "softcode",
            "SoftCode1\n(from the Pi)",
            dict(dx=0.2, dy=-0.5),
        ),
        ("wait_response", "exit", "Tup", dict(dx=0.35)),
        ("ttl", "exit_t", "Tup", dict(dx=0.3, dy=0.3)),
        ("softcode", "exit_t", "Tup", dict(dx=0.3, dy=-0.3)),
    ],
    footer=[
        "An output not listed in the next state turns off automatically (LEDs, "
        "valve, BNC1).",
        "after_trial(): received = ttl / softcode / none;  water = 0",
    ],
)

# -------------------------------------------------------------- purge ports
SPECS["bpod_purge_ports"] = dict(
    size=(14, 9.0),
    title="BpodPurgePorts — state machine (one trial)",
    subtitle="Not a training task: a valve stays open while its port is poked, to "
    "flush the water lines.",
    nodes={
        "start": dict(kind="start", xy=(0.7, 4.2)),
        "ready_to_purge": dict(xy=(3.5, 4.2), lines=["timer: none", "out: none"]),
        "left_open": dict(
            xy=(8.2, 6.6), lines=["timer: none", "out: Valve1"], kind="reward"
        ),
        "center_open": dict(
            xy=(8.2, 4.2), lines=["timer: none", "out: Valve2"], kind="reward"
        ),
        "right_open": dict(
            xy=(8.2, 1.8), lines=["timer: none", "out: Valve3"], kind="reward"
        ),
        "exit": dict(kind="exit", xy=(12.6, 4.2)),
    },
    edges=[
        ("start", "ready_to_purge", ""),
        ("ready_to_purge", "left_open", "Port1In", dict(dx=-0.3, dy=0.3)),
        ("ready_to_purge", "center_open", "Port2In", dict(dy=0.3)),
        ("ready_to_purge", "right_open", "Port3In", dict(dx=-0.3, dy=-0.3)),
        ("left_open", "exit", "Port1Out", dict(dx=0.3, dy=0.3)),
        ("center_open", "exit", "Port2Out", dict(dy=0.3)),
        ("right_open", "exit", "Port3Out", dict(dx=0.3, dy=-0.3)),
    ],
    footer=[
        "after_trial(): outcome = left / center / right / none;  water = 0",
    ],
)

# -------------------------------------------------------------- touchscreen
SPECS["bpod_touchscreen"] = dict(
    size=(14.5, 9.0),
    title="BpodTouchscreen — state machine (one trial)",
    subtitle="Two rectangles: touching the long one (green) gives water; the short "
    "one (red) disappears sooner.",
    nodes={
        "start": dict(kind="start", xy=(0.7, 4.2)),
        "show_rects": dict(
            xy=(3.9, 4.2),
            lines=["timer: long_duration", "out: SoftCode19", "(draw both rectangles)"],
        ),
        "reward": dict(
            xy=(9.0, 6.6), lines=["timer: valve time", "out: Valve2"], kind="reward"
        ),
        "no_reward": dict(xy=(9.0, 4.2), lines=["timer: 0", "out: none"]),
        "miss": dict(xy=(9.0, 1.8), lines=["timer: 0", "out: none"]),
        "exit": dict(kind="exit", xy=(13.0, 4.2)),
    },
    edges=[
        ("start", "show_rects", ""),
        ("show_rects", "reward", "SoftCode1\n(touched long)", dict(dx=-0.5, dy=0.45)),
        ("show_rects", "no_reward", "SoftCode2\n(touched short)", dict(dy=0.45)),
        ("show_rects", "miss", "Tup (no touch)", dict(dx=-0.5, dy=-0.35)),
        ("reward", "exit", "Tup", dict(dx=0.25, dy=0.25)),
        ("no_reward", "exit", "Tup", dict(dy=0.3)),
        ("miss", "exit", "Tup", dict(dx=0.25, dy=-0.25)),
    ],
    footer=[
        "The touches reach Bpod as softcodes sent from touch_trigger.py.",
        "after_trial(): outcome = correct / incorrect / miss;  water only if correct",
    ],
)


if __name__ == "__main__":
    out = (
        sys.argv[1]
        if len(sys.argv) > 1
        else str(Path(__file__).parent.parent / "source" / "_static" / "examples")
    )
    for name, spec in SPECS.items():
        draw(spec, f"{out}/{name}_sm.png")
        print("ok", name)
