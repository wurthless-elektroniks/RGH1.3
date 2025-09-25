-- EXT_CLK Code for Matrix/Coolrunner, Phat 192 MHz Version
-- 15432, GliGli, Octal450
-- modified by wurthless elektroniks for EXT+3

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- main module

entity post_proc is
	Port (
		callback : in STD_LOGIC;
		POST : in STD_LOGIC;
		CLK : in STD_LOGIC;
		to_slow : out STD_LOGIC := '0';
		DBG : out STD_LOGIC := '0';
		RST : inout STD_LOGIC := 'Z'
	);
end post_proc;

architecture arch of post_proc is

-- pulse width of 2 or 3 works, anything wider/shorter won't work
constant R_LEN : integer := 2;

-- build for values 117998 ~ 118010
constant R_END : integer := 118002; -- Xenon: 118002, Zephyr: 118008

constant T_BUF : integer := 50000;
constant T_END : integer := R_END + T_BUF;

constant post_rgh : integer := 24;
constant post_max : integer := 31;
signal cnt : integer range 0 to T_END := 0;
signal post_cnt : integer range 0 to post_max := 0;
signal timeout : STD_LOGIC := '0';

begin

-- post counter
process (POST, post_cnt) is
begin
	if (POST'event) then
		if (RST = '0') then
			post_cnt <= 0;
		else
			if (post_cnt < post_max) then
				post_cnt <= post_cnt + 1;
			end if;
		end if;
	end if;
	
	if (post_cnt < post_max) then
		DBG <= POST;
	else
		DBG <= '0';
	end if;
end process;

-- timing counter + reset
process (CLK) is
begin
	if (CLK'event) then -- 192 MHz
		if (post_cnt >= post_rgh) then
			if (cnt < T_END) then
				cnt <= cnt + 1;
				timeout <= '0';
			else
				timeout <= '1';
			end if;
		else
			cnt <= 0;
			timeout <= '0';
		end if;
		
		if (cnt >= R_END - R_LEN and cnt < R_END and callback = '1') then
			RST <= '0';
		else
			if (cnt = R_END) then
				RST <= '1';
			else
				RST <= 'Z';
			end if;
		end if;
	end if;
end process;

-- slowdown
process (post_cnt, timeout) is
begin
	if (post_cnt >= post_rgh - 1 and timeout = '0') then
		to_slow <= '1';
	else
		to_slow <= '0';
	end if;
end process;

end arch;
