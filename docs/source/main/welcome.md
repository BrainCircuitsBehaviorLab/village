<!-- ── SECTION 1: Intro ── -->
<div class="full-bleed" style="background: #f7f5ff; padding: 0.5rem 2rem; margin-bottom: 4px;">
<table style="border-collapse: collapse; border: none; width: 100%;">
<tr>
<td style="border: none; width: 50%; vertical-align: middle; padding-right: 30px;">
<img src="_static/illustration.png" style="width: 100%;" alt="Training Village">
</td>
<td style="border: none; vertical-align: top;">
<p>The Training Village is a 24/7 ecosystem for the automated training of rodents in complex cognitive tasks. Animals live in social groups and can individually access an operant chamber at any time—24/7, year-round—monitored via integrated RFID and video camera tracking.</p>
<ul>
<li><strong>Welfare:</strong> Eliminates human handling and transport, providing the stable and predictable conditions required for optimal cognitive testing.</li>
<li><strong>Productivity:</strong> A single system supports 10–12 animals simultaneously, significantly reducing labor hours.</li>
<li><strong>Real-Time Monitoring:</strong> Access live feeds via VNC and receive instant status updates or alerts through Telegram.</li>
<li><strong>Open-Source &amp; Flexible:</strong> Designed to integrate with your specific protocols (Python-compatible). Fully open-source under <a href="https://www.gnu.org/licenses/quick-guide-gplv3.pdf">GPL version 3</a> and <a href="https://oshwa.org/resources/open-source-hardware-definition/">OSHW version 1</a> licenses.</li>
</ul>
</td>
</tr>
</table>
</div>

<!-- ── SECTION 2: Video ── -->
<div style="padding: 2.5rem 2rem; margin-bottom: 4px; text-align: center;">
<video controls width="80%" poster="_static/video_poster.png" style="display: inline-block;">
  <source src="_static/video.m4v" type="video/mp4">
</video>
</div>

<!-- ── SECTION 3: How Does It Work? ── -->
<div class="full-bleed" style="background: #f7f5ff; padding: 2rem 2rem 0.5rem 2rem; margin-bottom: 4px;">
<h1 style="font-size: 1.6rem;">How Does It Work?</h1>
<table style="border-collapse: collapse; border: none; width: 100%;">
<tr>
<td style="border: none; width: 55%; vertical-align: top; padding-right: 30px;">
<img src="_static/training_village.png" style="width: 100%;" alt="Training Village diagram">
</td>
<td style="border: none; vertical-align: top;">
<p>The system is composed of several key components: the housing where the animals live, the behavioral box where tasks are performed, and the corridor that regulates access to the behavioral box.</p>
<p>The Training Village is designed to wrap around your own task protocols and integrate with your behavioral control system although we provide it in tandem with a general-purpose touchscreen chamber and some standard task protocols run by BPod (by <a href="https://sanworks.io">Sanworks</a>).</p>
<p>Training Village is an open-source project. You can find the code in our <a href="https://github.com/BrainCircuitsBehaviorLab/village/">GitHub repository</a> and all the necessary resources to build it in the <a href="/resources_index.rst">resources section</a>.</p>
<h2>The Housing</h2>
<p>The animals live together in one or more cages, which promotes better welfare. Any type of cage can be used, as long as it is connected to the corridor via a tube. We offer a solution with 2 or 4 cages connected by transparent acrylic tubes, which can serve different purposes (e.g., one cage with food, another for nesting). Optionally, RFID sensors can be installed in the tubes connecting the cages (<a href="https://elifesciences.org/articles/19532">Eco-HAB</a>) to gather more data on the animals' social behavior.</p>
<h2>The Corridor</h2>
<p>This is the central part of the system, consisting of a plastic corridor equipped with an RFID sensor, a weight scale, and a camera. Using a mechanism with two doors, animals can enter the behavioral box under certain conditions. The corridor sizes, shape and the motorized doors have been exhaustively tested and improved to efficiently control single-animal entrances using the minimum space possible. The entire system is controlled by a Raspberry Pi, which handles sending and receiving signals from electronic devices, controls the cameras, and runs the software that controls the whole system. Most of the elements in the mouse version of the corridor are 3D-printed, except for the doors and the corridor lid, which are made of white laser-cut acrylic. The design files are shared in the How to build the training village (link) section. We also share the rat version, which includes more laser-cut parts and fewer printed components due to its larger size and the increased strength required.</p>
<h2>The Behavioral Box</h2>
<p>Any type of behavioral box can be used. We provide two design options: one with auditory stimuli and three behavioral ports, and another with a touchscreen and one reward port. The system is designed to interact with behavioral boxes controlled by Bpod (using Python). Integration with other controllers, such as Bcontrol or Bonsai, is currently under development.</p>
<p>The software that controls the system runs reliably 24/7 while monitoring the animals, regulating their access to the behavioral box, initiating tasks, and updating data.</p>
<p>We determined that the best option for running this system is the Raspberry Pi, due to its reliability, low power consumption, and cost-effectiveness. These mini-computers are designed to excel in tasks like these, come equipped with specialized video cameras, and can interact with a wide range of electronic devices.</p>
<p>To simplify interaction with the hardware components, we have designed a custom Raspberry Pi HAT (Hardware Attached on Top). This HAT provides the necessary connectors to control two servo motors, an RFID reader, a weight sensor, and a temperature sensor. This setup ensures seamless device connectivity, delivering a plug-and-play experience.</p>
</td>
</tr>
</table>
</div>


<!-- ── SECTION 4: System Usage ── -->
<div style="padding: 2.5rem 2rem; margin-bottom: 4px;">
<h1 style="font-size: 1.6rem;">System Usage</h1>
<p>The Training Village has been rigorously tested in the <a href="https://braincircuitsbehavior.org">Brain Circuits and Behavior Lab</a> across multiple cohorts of mice and three distinct behavioral paradigms: a three-choice visuospatial delayed response task, a two-choice visual or auditory perceptual discrimination task, and a two-armed bandit task. The system has been successfully adapted to rats in the <a href="https://www.uab.cat/en/incuab/fx-animalmindslab-en">Animal Minds Lab</a>.</p>
<img src="_static/plots.png" style="width: 100%;" alt="System usage plots">
</div>

<!-- ── SECTION 5: Citing ── -->
<div class="full-bleed" style="background: #f7f5ff; padding: 2rem 2rem 1.5rem 2rem; margin-bottom: 4px;">
<h1 style="font-size: 1.6rem;">Citing Training Village</h1>
<p>If you use <strong>Training Village</strong>, please cite:</p>
<p>Serrano-Porcar, B., Marin, R., Rodríguez, J., Barezzi, C., Vasoya, H., Kean, D., Pottinger, D., Taylor, A., Martínez Vergara, H., &amp; de la Rocha, J. (2026).<br>
<em>The Training Village: an open platform for continuous testing of rodents in cognitive tasks.</em><br>
<strong>bioRxiv</strong>. <a href="https://doi.org/10.64898/2026.01.12.698970">https://doi.org/10.64898/2026.01.12.698970</a></p>
</div>

<!-- ── SECTION 6: About the Project ── -->
<div style="padding: 2.5rem 2rem; margin-bottom: 4px;">

<p><strong>Developed by:</strong></p>
<a href="https://braincircuitsbehavior.org"
style="color:#8B00FF; font-size:24px; font-weight:normal;
font-family:'Futura', sans-serif; text-decoration:none;">
BRAIN CIRCUITS AND BEHAVIOR LAB
</a>
<p style="margin-top: 1.5rem;">Funding was provided by the Spanish State Research Agency (AEI), the European Research Council (ERC), and the Cellex Foundation.</p>
<div style="display: flex; justify-content: center; align-items: center; gap: 40px; max-width: 600px; margin: 20px auto 20px auto;">
  <img src="_static/AEI.png" alt="AEI logo" style="height: 70px;">
  <img src="_static/ERC.png" alt="ERC logo" style="height: 70px;">
  <img src="_static/CELLEX.png" alt="Cellex logo" style="height: 70px;">
</div>
