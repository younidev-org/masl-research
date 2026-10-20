
; ============================================================
; TUMOR-IMMUNE MICROENVIRONMENT
; Agent-Based Adaptive Modelling + Multi-Agent Systems
; Simplified educational model


; Agent	Color	Behavior
; Tumor cell	Red	Proliferates, consumes resources, develops resistance, sends suppression signals
; Cytotoxic T cell	Cyan	Searches for tumor cells, receives activation signals, attacks, requests assistance
; Macrophage	Green / Orange	Switches between simplified M1/M2 states, activates or suppresses immune responses
; Environment agent	Hidden	Monitors local hypoxia and broadcasts environmental information
; ============================================================

breed [tumor-cells tumor-cell]
breed [t-cells t-cell]
breed [macrophages macrophage]
breed [environment-agents environment-agent]

globals [

  immune-strength
  tumor-division-probability
  immune-kills
  messages-sent
]

patches-own [
  oxygen
  nutrients
  cytokine
  vessel?
]

turtles-own [
  inbox
  cell-age
]

tumor-cells-own [
  energy
  resistance
]

t-cells-own [
  activation
  exhaustion
]

macrophages-own [
  phenotype
]


; ============================================================
; 1. INITIALIZATION
; ============================================================

to setup
  setup-with 60 40 20 0.15 0.45
end

to setup-with [n-tumors n-tcells n-macrophages supply strength]
  clear-all

  set oxygen-input supply
  set immune-strength strength
  set tumor-division-probability 0.12
  set immune-kills 0
  set messages-sent 0

  ; Initialize the spatial environment.
  ask patches [
    set oxygen (0.20 + random-float 0.35)
    set nutrients (0.20 + random-float 0.40)
    set cytokine 0
    set vessel? false
  ]

  ; Simplified vascular nutrient/oxygen sources.
  ask n-of 26 patches [
    set vessel? true
    set oxygen 1
    set nutrients 1
  ]

  ; Create tumor population near the center.
  create-tumor-cells n-tumors [
    setxy (random-float 8 - 4) (random-float 8 - 4)
    set shape "circle"
    set color red
    set size 0.85

    set energy 0.70
    set resistance 0.05
    set cell-age 0
    set inbox []
  ]

  ; Create cytotoxic T cells.
  create-t-cells n-tcells [
    setxy random-xcor random-ycor
    set shape "circle"
    set color cyan
    set size 0.85

    set activation 0.45
    set exhaustion 0
    set cell-age 0
    set inbox []
  ]

  ; Create macrophages.
  create-macrophages n-macrophages [
    setxy random-xcor random-ycor
    set shape "circle"
    set color green
    set size 1.1

    set phenotype "M1"
    set cell-age 0
    set inbox []
  ]

  ; A logical environment agent monitors hypoxia.
  create-environment-agents 1 [
    set inbox []
    set cell-age 0
    hide-turtle
  ]

  recolor-environment
  reset-ticks
end


; ============================================================
; 2. MAIN SIMULATION LOOP
; ============================================================

to go
  if not any? tumor-cells [ stop ]
  if ticks >= 300 [ stop ]

  ; Update chemical fields and send environmental messages.
  environment-step

  ; Macrophages send activation/support signals.
  ask macrophages [
    macrophage-step
  ]

  ; Tumors adapt, proliferate, and signal.
  ask tumor-cells [
    tumor-step
  ]

  ; T cells receive signals and attack.
  ask t-cells [
    tcell-step
  ]

  ; Tumors resolve accumulated immune attacks.
  ask tumor-cells [
    resolve-attacks
  ]

  recolor-environment
  tick
end


; ============================================================
; 3. ENVIRONMENT
; ============================================================

to environment-step

  ; Blood vessels replenish resources.
  ask patches with [vessel?] [
    set oxygen min (list 1 (oxygen + oxygen-input))
    set nutrients min (list 1 (nutrients + oxygen-input))
  ]

  ; Spatial diffusion is executed by the observer.
  diffuse oxygen 0.28
  diffuse nutrients 0.18
  diffuse cytokine 0.35

  ; Cytokines decay over time.
  ask patches [
    set cytokine cytokine * 0.93
  ]

  ; Environment agent broadcasts local hypoxia warnings.
  ask environment-agents [
    let targets (turtle-set tumor-cells t-cells macrophages)
      with [ [oxygen] of patch-here < 0.25 ]

    foreach (sort targets) [target ->
      send-message target "inform" "hypoxia" 0.03
    ]
  ]
end


; ============================================================
; 4. AGENT COMMUNICATION
; Message format:
; [sender-id, performative, topic, magnitude]
; ============================================================

to send-message [recipient performative topic magnitude]
  if recipient != nobody [
    let message (list who performative topic magnitude)

    ask recipient [
      set inbox lput message inbox
    ]

    set messages-sent messages-sent + 1
  ]
end


; ============================================================
; 5. RESOURCE CONSUMPTION
; ============================================================

to consume-resources [oxygen-demand nutrient-demand]
  ask patch-here [
    set oxygen max (list 0 (oxygen - oxygen-demand))
    set nutrients max (list 0 (nutrients - nutrient-demand))
  ]
end


; ============================================================
; 6. MACROPHAGE AGENT
; ============================================================

to macrophage-step
  set cell-age cell-age + 1

  consume-resources 0.008 0.009

  let local-tumors count (tumor-cells in-radius 4)
  let local-oxygen [oxygen] of patch-here

  ; Simplified phenotype adaptation:
  ; hypoxia with nearby tumor cells favors M2.
  ifelse (local-oxygen < 0.35 and local-tumors > 1) [
    set phenotype "M2"
    set color orange
  ] [
    set phenotype "M1"
    set color green
  ]

  ; Process assistance requests from T cells.
  foreach inbox [message ->
    if (item 1 message = "request") and
       (item 2 message = "help") and
       (phenotype = "M1") [

      let requester turtle (item 0 message)

      if requester != nobody [
        send-message requester "inform" "activate" 0.15
      ]
    ]
  ]

  set inbox []

  ; M1 macrophages stimulate nearby T cells.
  if phenotype = "M1" [
    foreach (sort (t-cells in-radius 3)) [target ->
      send-message target "inform" "activate" 0.10
    ]
  ]

  ; M2 macrophages suppress immunity and support tumors.
  if phenotype = "M2" [
    foreach (sort (t-cells in-radius 3)) [target ->
      send-message target "inform" "suppress" 0.08
    ]

    foreach (sort (tumor-cells in-radius 2)) [target ->
      send-message target "inform" "support" 0.025
    ]
  ]

  ; Move toward nearby tumor cells.
  ifelse any? (tumor-cells in-radius 7) [
    let target min-one-of (tumor-cells in-radius 7)
      [distance myself]

    face target
    forward 0.35
  ] [
    right (random 61 - 30)
    forward 0.4
  ]

  ; Simplified age-related cell loss.
  if cell-age > 250 and random-float 1 < 0.015 [
    die
  ]
end


; ============================================================
; 7. TUMOR CELL AGENT
; ============================================================

to tumor-step
  set cell-age cell-age + 1

  let available min
    (list ([oxygen] of patch-here)
          ([nutrients] of patch-here))

  ; Resource-dependent energy balance.
  set energy energy + (0.11 * available) - 0.045

  consume-resources 0.022 0.024

  ; Process messages from the environment and macrophages.
  foreach inbox [message ->

    if item 2 message = "hypoxia" [
      set resistance min
        (list 0.85 (resistance + 0.02))
    ]

    if item 2 message = "support" [
      set energy min
        (list 1.6 (energy + item 3 message))
    ]
  ]

  set inbox []

  ; Tumor adaptation to local environmental stress.
  if available < 0.30 [
    set resistance min
      (list 0.85 (resistance + 0.008))
  ]

  if available > 0.60 [
    set resistance max
      (list 0 (resistance - 0.002))
  ]

  ; Tumor cells release a local signaling field.
  ask patch-here [
    set cytokine min (list 1 (cytokine + 0.09))
  ]

  ; Resistant tumors suppress nearby immune cells.
  if resistance > 0.20 [
    foreach (sort (t-cells in-radius 2)) [target ->
      send-message target "inform" "suppress" 0.06
    ]
  ]

  ; Starvation and resource-stress death.
  if energy <= 0 [
    die
    stop
  ]

  if available < 0.12 and random-float 1 < 0.02 [
    die
    stop
  ]

  ; Proliferation by cell division.
  if energy > 1.05 and
     random-float 1 < tumor-division-probability and
     count tumor-cells < 650 [

    set energy energy / 2

    hatch 1 [
      right random 360
      forward 0.8
      set size 0.85
      set color red
      set inbox []
      set cell-age 0
    ]
  ]
end


; ============================================================
; 8. CYTOTOXIC T CELL AGENT
; ============================================================

to tcell-step
  set cell-age cell-age + 1

  consume-resources 0.006 0.007

  ; Natural decay of activation and exhaustion.
  set activation max (list 0 (activation - 0.012))
  set exhaustion max (list 0 (exhaustion - 0.03))

  ; Process incoming messages.
  foreach inbox [message ->

    if item 2 message = "activate" [
      set activation min
        (list 1 (activation + item 3 message))
    ]

    if item 2 message = "suppress" [
      set activation max
        (list 0 (activation - item 3 message))
    ]

    if item 2 message = "hypoxia" [
      set exhaustion min
        (list 1 (exhaustion + item 3 message))
    ]
  ]

  set inbox []

  ; Search for tumor cells.
  ifelse any? (tumor-cells in-radius 7) [

    let target min-one-of (tumor-cells in-radius 7)
      [distance myself]

    face target
    forward 0.75

  ] [

    ; Follow the local cytokine concentration gradient.
    let destination max-one-of
      ([neighbors] of patch-here) [cytokine]

    face destination
    forward 0.7
  ]

  ; Request macrophage assistance if insufficiently active.
  if activation < 0.60 and
     any? (macrophages in-radius 4) [

    let partner min-one-of (macrophages in-radius 4)
      [distance myself]

    send-message partner "request" "help" 0.12
  ]

  ; Attack a nearby tumor cell.
  if activation > 0.10 and
     any? (tumor-cells in-radius 1.25) [

    let target min-one-of (tumor-cells in-radius 1.25)
      [distance myself]

    let damage immune-strength * activation *
      (1 - exhaustion)

    if damage > 0 [
      send-message target "inform" "damage" damage

      set exhaustion min
        (list 1 (exhaustion + 0.10))
    ]
  ]

  ; Simplified survival rule.
  if ([oxygen] of patch-here < 0.10) and
     (random-float 1 < 0.02) [
    die
    stop
  ]

  if cell-age > 220 and random-float 1 < 0.015 [
    die
  ]
end


; ============================================================
; 9. RESOLVE IMMUNE ATTACKS
; ============================================================

to resolve-attacks
  let accumulated-damage 0

  ; Aggregate messages received during this tick.
  foreach inbox [message ->
    if item 2 message = "damage" [
      set accumulated-damage
        accumulated-damage + item 3 message
    ]
  ]

  set inbox []

  if accumulated-damage > 0 [

    ; Tumor resistance reduces effective attack strength.
    let kill-probability min
      (list 0.95
        (accumulated-damage * (1 - resistance)))

    if random-float 1 < kill-probability [
      set immune-kills immune-kills + 1
      die
    ]
  ]
end


; ============================================================
; 10. VISUALIZATION
; ============================================================

to recolor-environment
  ask patches [
    set pcolor scale-color blue oxygen 0 1

    if vessel? [
      set pcolor sky
    ]
  ]
end


; ============================================================
; 11. REPORTERS / METRICS
; ============================================================

to-report hypoxic-fraction
  report (count patches with [oxygen < 0.25]) /
    (count patches)
end

to-report mean-oxygen
  report mean [oxygen] of patches
end

to-report mean-nutrients
  report mean [nutrients] of patches
end

to-report mean-tumor-resistance
  if not any? tumor-cells [ report 0 ]
  report mean [resistance] of tumor-cells
end

to-report m1-count
  report count macrophages with [phenotype = "M1"]
end

to-report m2-count
  report count macrophages with [phenotype = "M2"]
end
