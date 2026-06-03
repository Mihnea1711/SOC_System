-- Create a dummy table for users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) NOT NULL,
    credit_card VARCHAR(20) NOT NULL,
    ssn VARCHAR(11) NOT NULL
);

-- Insert a large amount of dummy data to simulate a real database
-- This ensures that a "SELECT *" query generates a massive payload response
-- which our ML model will flag as an anomaly (Data Exfiltration)

DELIMITER $$
CREATE PROCEDURE InsertDummyData()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 5000 DO
        INSERT INTO users (username, password_hash, email, credit_card, ssn)
        VALUES (
            CONCAT('user_', i),
            MD5(RAND()),
            CONCAT('user_', i, '@example.com'),
            CONCAT(
                LPAD(FLOOR(RAND() * 9999), 4, '0'), '-',
                LPAD(FLOOR(RAND() * 9999), 4, '0'), '-',
                LPAD(FLOOR(RAND() * 9999), 4, '0'), '-',
                LPAD(FLOOR(RAND() * 9999), 4, '0')
            ),
            CONCAT(
                LPAD(FLOOR(RAND() * 999), 3, '0'), '-',
                LPAD(FLOOR(RAND() * 99), 2, '0'), '-',
                LPAD(FLOOR(RAND() * 9999), 4, '0')
            )
        );
        SET i = i + 1;
    END WHILE;
END$$
DELIMITER ;

CALL InsertDummyData();
DROP PROCEDURE InsertDummyData;
