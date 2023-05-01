<?php
header('Content-Type: application/json');
// ini_set("log_errors", 1);
// ini_set("error_log", "/tmp/php-error.log");
require_once "db_credentials.php";
$mysqli = new mysqli($DBhostname, $DBusername, $DBpassword, $DBname, $DBport);
if($mysqli->connect_error) {
  exit('Could not connect');
}

$category1 = $_GET['cat1'];
$category2 = $_GET['cat2'];
$query = sprintf("SELECT $category1, $category2, Date FROM lik_kvpi_evolution ORDER BY Date");
$result = $mysqli->query($query);
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
