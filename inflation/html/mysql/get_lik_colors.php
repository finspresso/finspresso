<?php
header('Content-Type: application/json');
define('DB_HOST', 'localhost');
define('DB_USERNAME', 'root');
define('DB_PASSWORD', '');
define('DB_NAME', 'dummy');
$mysqli = new mysqli(DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME);
if($mysqli->connect_error) {
  exit('Could not connect');
}

$sql = "SELECT * FROM `lik_colors` LIMIT 1";
$result = $mysqli->query($sql);
// while($row = mysqli_fetch_array($result)){
//     echo $row['Field']."<br>";
// }
//loop through the returned data
$data = array();
foreach ($result as $row) {
	$data[] = $row;
}

//free memory associated with result
$result->close();

//close connection
$mysqli->close();
print json_encode($data);
?>
