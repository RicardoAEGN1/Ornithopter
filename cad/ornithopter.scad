// ============================================================
//  ORNITHOPTER — Drone estilo Dune (thopter)
//  Modelo CAD paramétrico (OpenSCAD) — chassi + carenagem
//  Abre em OpenSCAD (gratuito) e exporta STL para impressão 3D
// ============================================================

/* [Dimensões principais — mm] */
motor_spacing = 78;      // distância motor-a-motor (diagonal X)
arm_width     = 8;       // largura do braço
plate_t       = 2.0;     // espessura das placas (PLA)
motor_d       = 8.5;     // diâmetro do motor 8520
motor_h       = 20;      // altura do motor 8520
prop_d        = 65;      // hélice 65 mm
ring_w        = 3.2;     // espessura do anel de proteção (gondola)
canopy_h      = 14;      // altura da carenagem estilo thopter
hole_m2       = 2.2;     // furo M2 para motores

$fn = 64;

// ---------- Módulos ----------

// Braço do frame X (entre dois motores opostos)
module arm(len) {
    rotate([0,0,45])
        cube([len, arm_width, plate_t], center=true);
}

// Suporte do motor: anel + furos M2
module motor_mount() {
    difference() {
        cylinder(d = motor_d + 5, h = plate_t, center = true);
        cylinder(d = motor_d - 1.2, h = plate_t + 1, center = true); // cavity motor
        for (a = [0, 90, 180, 270])
            rotate([0, 0, a + 45])
                translate([(motor_d + 3) / 2, 0, 0])
                    cylinder(d = hole_m2, h = plate_t + 2, center = true);
    }
}

// Anel de proteção da hélice (gondola estilo Dune)
module prop_ring() {
    rotate_extrude()
        translate([prop_d/2 + 4, 0, 0])
            circle(d = ring_w);
}

// Corpo central: duas placas + espaçadores
module body() {
    half = motor_spacing / 2;
    // braços em X
    arm(motor_spacing * 1.45);
    mirror([0,1,0]) arm(motor_spacing * 1.45);
    // placa inferior
    translate([0, 0, -plate_t/2 - 6])
        cube([34, 34, plate_t], center = true);
    // placa superior
    translate([0, 0, plate_t/2 + 6])
        cube([34, 34, plate_t], center = true);
}

// Carenagem estilo "thopter": casco alongado com quilha
module canopy() {
    hull() {
        translate([0, 0, 8]) scale([1.6, 1, 0.55]) sphere(d = 22);
        translate([-26, 0, 4]) scale([1.2, 0.8, 0.4]) sphere(d = 16); // nariz
        translate([20, 0, 4]) scale([1.3, 0.85, 0.45]) sphere(d = 18); // cauda
    }
    // quilha ventral (estabilidade visual e antitombo)
    translate([0, 0, -1]) rotate([90, 0, 0])
        linear_extrude(height = 2, center = true)
            polygon([[-24,0],[24,0],[10,-9],[-14,-9]]);
}

// ---------- Montagem ----------

half = motor_spacing / 2;

module ornithopter() {
    body();
    // motores + anéis nos 4 cantos
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * half, sy * half, 0]) {
            prop_ring();
            translate([0, 0, motor_h/2 + plate_t/2])
                %cylinder(d = motor_d, h = motor_h, center = true); // motor (fantasma)
        }
    canopy();
}

// Plana: Vista de topo da placa única do frame (para imprimir)
module frame_flat() {
    difference() {
        union() {
            arm(motor_spacing * 1.45);
            mirror([0,1,0]) arm(motor_spacing * 1.45);
            cube([34, 34, plate_t], center = true);
        }
        // alívio de peso central
        translate([0, 0, 0]) cube([22, 14, plate_t + 2], center = true);
        // furos dos motores
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * half, sy * half, 0])
                for (a = [0, 90, 180, 270])
                    rotate([0, 0, a + 45])
                        translate([(motor_d + 3) / 2, 0, 0])
                            cylinder(d = hole_m2, h = plate_t + 2, center = true);
    }
}

// Escolher o que mostrar:
// ornithopter();   // vista completa com carenagem e anéis
frame_flat();       // vista da placa plana pronta a imprimir
