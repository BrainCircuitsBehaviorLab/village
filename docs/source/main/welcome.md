<!-- ── SECTION 1: Intro ── -->
<div style="padding: 0.5rem 2rem; margin-bottom: 4px;">
<p>The Training Village is a system designed for the continuous, automated training of rodents in complex cognitive tasks. RFID-tagged animals live in groups and individually access an operant box to perform tasks at any time, 24/7.</p>
<table style="border-collapse: collapse; border: none; width: 100%;">
<tr>
<td style="border: none; width: 50%; vertical-align: middle; padding-right: 30px;">
<img src="_static/illustration.png" style="width: 100%;" alt="Training Village">
</td>
<td style="border: none; vertical-align: top;">
<ul class="purple-bullets">
<li><strong style="font-size: 1.1rem; color: #8B00FF;">Flexibility:</strong> Designed to integrate with your specific Python protocols and behavioral control system. It is fully compatible with <a href="https://sanworks.io">Bpod (Sanworks)</a> or <a href="https://www.arduino.cc">Arduino</a> as your primary task controllers.</li>
<li><strong style="font-size: 1.1rem; color: #8B00FF;">Productivity:</strong> A single setup supports 10–12 animals simultaneously, significantly reducing manual labor hours.</li>
<li><strong style="font-size: 1.1rem; color: #8B00FF;">Welfare:</strong> Enhances animal well-being by allowing animals to live in social groups and by eliminating human handling and transport, providing the stable and predictable conditions required for optimal cognitive testing.</li>
<li><strong style="font-size: 1.1rem; color: #8B00FF;">Real-Time Monitoring:</strong> Check animal status at any time via integrated cameras. Receive instant updates and alerts directly through Telegram.</li>
<li><strong style="font-size: 1.1rem; color: #8B00FF;">Open-Source:</strong> Fully open-source under <a href="https://www.gnu.org/licenses/quick-guide-gplv3.pdf">GPL v.3</a> and <a href="https://oshwa.org/resources/open-source-hardware-definition/">OSHW v.1</a> licenses. Access the source code on <a href="https://github.com/BrainCircuitsBehaviorLab/village/">GitHub</a> and find detailed assembly plans in the <a href="resources_index.html">Resources</a> section.</li>
</ul>
</td>
</tr>
</table>
</div>

<!-- ── SECTION 2: Video ── -->
<div class="full-bleed" style="background: #f7f5ff; padding: 2.5rem 2rem; margin-bottom: 4px;">
<h1 style="font-size: 1.6rem;">Watch the System in Action</h1>
<div style="text-align: center;">
<video controls width="80%" style="display: inline-block;">
  <source src="_static/video.m4v" type="video/mp4">
</video>
</div>
</div>

<!-- ── SECTION 3: How Does It Work? (text) ── -->
<div style="padding: 2rem 2rem 1.5rem 2rem; margin-bottom: 4px;">
<h1 style="font-size: 1.6rem;">How Does It Work?</h1>
<table style="border-collapse: collapse; border: none; width: 100%; margin-bottom: 1rem;">
<tr>
<td style="border: none; width: 30%; vertical-align: middle; padding-right: 20px;">
<img src="_static/raspberry_hat.png" style="width: 100%;" alt="Raspberry Pi HAT">
</td>
<td style="border: none; vertical-align: middle;">
<p>The system is managed by a <a href="https://www.raspberrypi.com">Raspberry Pi</a>, selected for its reliability, low power consumption, and efficiency. This core unit is equipped with a custom Plug-and-Play HAT (Hardware Attached on Top), which seamlessly connects all sensors and actuators within the corridor.</p>
</td>
</tr>
</table>
<p><strong style="font-size: 1.1rem; color: #8B00FF;">Social Living &amp; Identification —</strong> Animals reside in social groups within one or more home cages. When an animal enters the access corridor, the setup utilizes RFID identification and a video camera to recognize the subject. A precision dual-door mechanism, orchestrated by the Raspberry Pi, ensures a controlled, single-animal entry into the Operant Box.</p>
<p><strong style="font-size: 1.1rem; color: #8B00FF;">The Training Session —</strong> Once the animal is inside, the task logic and hardware—such as behavioral water ports—are typically managed by Bpod or Arduino. Simultaneously, the Raspberry Pi performs real-time camera-based tracking, allowing the animal's position to trigger specific experimental events. Additionally, it provides the high-level processing power required for peripherals like touchscreens or sound cards, ensuring stimulus presentation with negligible latency.</p>
<p><strong style="font-size: 1.1rem; color: #8B00FF;">Return &amp; Data Synchronization —</strong> After the session, the animal returns to its social group. All data is automatically synchronized to a server or external drive, and the training parameters for that specific subject are updated. This ensures the animal advances through its training protocols without any manual intervention.</p>
<p><strong style="font-size: 1.1rem; color: #8B00FF;">Modular &amp; Extensible —</strong> The platform is built to grow with your research:</p>
<ul>
<li><strong>Social Behavior:</strong> Optional RFID sensors can be installed in the connecting tubes (<a href="https://elifesciences.org/articles/19532">Eco-HAB</a>) to track movement and facilitate deep social behavior analysis.</li>
<li><strong>Wireless Optogenetics:</strong> The setup supports seamless integration with wireless optogenetic implants (<a href="https://www.neurolux.org">NEUROLUX</a>).</li>
</ul>
</div>

<!-- ── SECTION 4: How Does It Work? (image) ── -->
<div class="full-bleed" style="background: #f7f5ff; padding: 1.5rem 2rem; margin-bottom: 4px; text-align: center;">
<img src="_static/training_village.png" style="width: 65%;" alt="Training Village diagram">
</div>


<!-- ── SECTION 5: System Usage ── -->
<div style="padding: 2.5rem 2rem; margin-bottom: 4px;">
<h1 style="font-size: 1.6rem;">System Usage</h1>
<p>The Training Village has been rigorously tested in the <a href="https://braincircuitsbehavior.org">Brain Circuits and Behavior Lab</a> across multiple cohorts of mice and three distinct behavioral paradigms: a three-choice visuospatial delayed response task, a two-choice visual or auditory perceptual discrimination task, and a two-armed bandit task. The system has been successfully adapted to rats in the <a href="https://www.uab.cat/en/incuab/fx-animalmindslab-en">Animal Minds Lab</a>.</p>
<img src="_static/plots.png" style="width: 100%;" alt="System usage plots">
</div>

<!-- ── SECTION 6: Citing ── -->
<div class="full-bleed" style="background: #f7f5ff; padding: 2rem 2rem 1.5rem 2rem; margin-bottom: 4px;">
<h1 style="font-size: 1.6rem;">Citing Training Village</h1>
<p>If you use <strong>Training Village</strong>, please cite:</p>
<p>Serrano-Porcar, B., Marin, R., Rodríguez, J., Barezzi, C., Vasoya, H., Kean, D., Pottinger, D., Taylor, A., Martínez Vergara, H., &amp; de la Rocha, J. (2026).<br>
<em>The Training Village: an open platform for continuous testing of rodents in cognitive tasks.</em><br>
<strong>bioRxiv</strong>. <a href="https://doi.org/10.64898/2026.01.12.698970">https://doi.org/10.64898/2026.01.12.698970</a></p>
</div>

<!-- ── SECTION 7: About the Project ── -->
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
