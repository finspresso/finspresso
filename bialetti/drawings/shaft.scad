    //shaft
    cylinder(h=2.5, r1=2.5, r2=2.5, center=false, $fn=100);
    translate([0, 0, 2.5])
    intersection() {
      cylinder(h=6, r1=2, r2=2, center=false, $fn=100);
      translate([-1.5, -5, 0.0])
      cube([3,10,6]);
    }
