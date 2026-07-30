<?php
echo json_encode(['raw' => file_get_contents('php://input'), 'decoded' => json_decode(file_get_contents('php://input'), true)]);