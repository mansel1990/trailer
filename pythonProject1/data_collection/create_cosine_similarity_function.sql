-- Create cosine similarity function for MySQL
-- This function calculates cosine similarity between two JSON arrays

DELIMITER $$

CREATE FUNCTION COSINE_SIMILARITY(vec1 JSON, vec2 JSON) 
RETURNS FLOAT
DETERMINISTIC
READS SQL DATA
COMMENT 'Calculate cosine similarity between two JSON arrays'
BEGIN
    DECLARE dot_product FLOAT DEFAULT 0;
    DECLARE norm1 FLOAT DEFAULT 0;
    DECLARE norm2 FLOAT DEFAULT 0;
    DECLARE i INT DEFAULT 0;
    DECLARE vec1_length INT DEFAULT JSON_LENGTH(vec1);
    DECLARE vec2_length INT DEFAULT JSON_LENGTH(vec2);
    DECLARE val1 FLOAT;
    DECLARE val2 FLOAT;
    
    -- Check if vectors have same length
    IF vec1_length != vec2_length THEN
        RETURN NULL;
    END IF;
    
    -- Calculate dot product and norms
    WHILE i < vec1_length DO
        SET val1 = JSON_EXTRACT(vec1, CONCAT('$[', i, ']'));
        SET val2 = JSON_EXTRACT(vec2, CONCAT('$[', i, ']'));
        
        SET dot_product = dot_product + (val1 * val2);
        SET norm1 = norm1 + (val1 * val1);
        SET norm2 = norm2 + (val2 * val2);
        
        SET i = i + 1;
    END WHILE;
    
    -- Calculate cosine similarity
    IF norm1 = 0 OR norm2 = 0 THEN
        RETURN 0;
    ELSE
        RETURN dot_product / (SQRT(norm1) * SQRT(norm2));
    END IF;
END$$

DELIMITER ; 