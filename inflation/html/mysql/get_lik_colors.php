<?php
header('Content-Type: application/json');
require_once "db_credentials_local.php";
$mysqli = new mysqli($DBhostname, $DBusername, $DBpassword, $DBname, $DBPort);
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
