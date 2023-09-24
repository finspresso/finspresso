tolerance = 1;
dial_breadth = 37 + tolerance;
dial_width = 11  + tolerance ;
dial_height = 7 + tolerance;



offset_r = 2.5;
offset_height = 2.5;
shaft_flat_height = 6;
shaft_flat_r = 2.5;
total_height_shaft = shaft_flat_height + offset_height;


interface_breadth = dial_breadth * 5 / 4;
interface_width = dial_width * 6 / 4;
interface_height = shaft_flat_height + dial_height;


inter_cube_x = shaft_flat_r * 5;
inter_cube_y = 1.7 * 2;

//shaft
translate([0, 0, -offset_height])
cylinder(h=offset_height, r1=offset_r, r2=offset_r, center=false, $fn=100);

intersection() {
  cylinder(h=shaft_flat_height + tolerance, r1=shaft_flat_r, r2=shaft_flat_r, center=false, $fn=100);
  translate([-inter_cube_x / 2, -inter_cube_y / 2, 0.0])
  cube([inter_cube_x, inter_cube_y, shaft_flat_height + tolerance]);
}

// Chamfer
chamfer_height = 1.0;
cylinder(h=chamfer_height, r1=offset_r + 1, r2=inter_cube_y / 2, center=false, $fn=100);
