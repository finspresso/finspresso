// shaft dia = 5
// flat bit = 3
// length = 8.5
// flat length = 6
tolerance = 2;
dial_height = 37;
hearth_thickness = 39.6;
hearth_offset_origin = 97; //102.5 - dial_height / 2;
housing_diameter = 28.4;
support_breadth =  44;
support_height = 5;
hole_offset = 17.5;
hole_tolerance = 0.15;
hole_diameter = 4.2;
interface_thickness = 4;
protrusion = interface_thickness + 25;
protrusion_thickness = 5;
support_offset = 6;
support_width = hearth_offset_origin + hearth_thickness + protrusion_thickness;// + support_offset;





difference(){
    union() {
        translate([-support_breadth / 2, -support_offset, 0 ])
        cube(size = [support_breadth, support_width, support_height], center = false);
        translate([-support_breadth / 2, hearth_offset_origin - protrusion_thickness - support_offset, support_height ])
        cube(size = [support_breadth, protrusion_thickness, protrusion], center = false);
        translate([-support_breadth / 2, hearth_offset_origin - support_offset + hearth_thickness, support_height ])
        cube(size = [support_breadth, protrusion_thickness, protrusion], center = false);
    }

    // Holes
    translate([-hole_offset, 0, -0.1])
    cylinder(h=support_height + tolerance, d1=hole_diameter, d2=hole_diameter, center=false, $fn=100);
    translate([hole_offset, 0, -0.1])
    cylinder(h=support_height + tolerance, d1=hole_diameter, d2=hole_diameter, center=false, $fn=100);

    // Motor housing
    translate([0, 0, -0.1])
    cylinder(h=support_height + tolerance, d1=housing_diameter, d2=housing_diameter, center=false, $fn=100);
}
