<?php

// ini_set("log_errors", 1);
ini_set("error_log", "/tmp/php-error.log");
header('Content-Type: application/json');

require_once "db_credentials.php";
$mysqli = new mysqli($DBhostname, $DBusername, $DBpassword, $DBname, $DBport);
if($mysqli->connect_error) {
  exit('Could not connect');
}
$desired_category = $_GET['q'];
//error_log("Test category: $test_category", 0);
$query = sprintf("SHOW COLUMNS FROM $desired_category");
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
