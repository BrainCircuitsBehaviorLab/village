<!-- ── SECTION 1: Intro ── -->
<div style="padding: 0.5rem 2rem; margin-bottom: 4px;">
<table style="border-collapse: collapse; border: none; width: 100%;">
<tr>
<td style="border: none; width: 50%; vertical-align: middle; padding-right: 30px;">
<img src="_static/illustration.png" style="width: 100%;" alt="Training Village">
</td>
<td style="border: none; vertical-align: top;">
<p>The Training Village is designed for the continuous, automated training of rodents in complex cognitive tasks. RFID-tagged animals live in social groups and individually access an operant box at any time, 24/7.</p>
<ul>
<li><strong>Welfare:</strong> Eliminates human handling and transport, providing the stable and predictable conditions required for optimal cognitive testing.</li>
<li><strong>Productivity:</strong> A single system supports 10–12 animals simultaneously, significantly reducing labor hours.</li>
<li><strong>Real-Time Monitoring:</strong> Access live feeds via VNC and receive instant status updates or alerts through Telegram.</li>
<li><strong>Open-Source &amp; Flexible:</strong> Designed to integrate with your specific protocols (Python-compatible). Fully open-source under <a href="https://www.gnu.org/licenses/quick-guide-gplv3.pdf">GPL version 3</a> and <a href="https://oshwa.org/resources/open-source-hardware-definition/">OSHW version 1</a> licenses. Access the source code on <a href="https://github.com/BrainCircuitsBehaviorLab/village/">GitHub</a> and find detailed assembly plans in the <a href="resources_index.html">Resources</a> section.</li>
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

<p>Animals reside in social groups within multiple cages connected by transparent tubes, creating specialized zones for nesting, feeding, and social interaction. These cages lead directly to the Access Corridor, the system’s "brain." This module uses RFID identification, video cameras, a precision weight scale, and a dual-door mechanism to manage controlled, single-animal entries into the Operant Box.</p>
<p>The entire process is orchestrated by a Raspberry Pi equipped with a custom Plug-and-Play HAT (Hardware Attached on Top), which connects all sensors and actuators within the corridor. The Raspberry Pi manages all electronic signals, controls the cameras, and runs the core system software. After each task, the system automatically synchronizes data to a server or external drive and updates the specific training parameters for that subject. The system remains fully accessible via remote control at all times.</p>
<p>The Training Village is highly versatile and can be used with any operant box controlled by Python scripts. While the system is perfectly integrated with Bpod (Sanworks) for task control, other controllers like Arduino can also be implemented. Crucially, the system operates without the need for an external PC; peripherals such as sound cards or touchscreens for stimulus presentation are controlled directly by the Raspberry Pi with negligible latency.</p>
<p>The platform is easily extensible to meet advanced research needs. For example, it can integrate Wireless Optogenetics (<a href="https://www.neurolux.org">NEUROLUX</a>) or facilitate deep social behavior analysis by incorporating additional RFID antennas to track animal movement within the home cages (<a href="https://elifesciences.org/articles/19532">ECO-HAB</a>).</p>

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
