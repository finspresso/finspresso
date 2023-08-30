// shaft dia = 5
// flat bit = 3
// length = 8.5
// flat length = 6

tolerance = 2;
dial_height = 37 + tolerance;
dial_width = 20 + tolerance ;
dial_breadth = 10 + tolerance;

interface_thickness = 4;
interface_height = 10;



difference(){
    translate([-dial_breadth * 2 / 2, -dial_width * 2 / 2, ])
    cube(size = [dial_breadth * 2, dial_width * 2, interface_height], center = false);

    // dial
    translate([-dial_breadth / 2, -dial_width / 2, interface_thickness])
    cube(size = [dial_breadth, dial_width, dial_height], center = false);


    //shaft
    translate([0, 0, -0.1])
    cylinder(h=2.5, r1=2.5, r2=2.5, center=false, $fn=100);
    translate([0, 0, 2.5])
    intersection() {
      cylinder(h=6, r1=2, r2=2, center=false, $fn=100);
      translate([-1.5, -5, 0.0])
      cube([3,10,6]);
    }
}
