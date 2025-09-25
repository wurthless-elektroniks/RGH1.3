library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- EXT_CLK slowdown + delayer

entity slower is
	Port (
		in_slow : in STD_LOGIC;
		CLK : in STD_LOGIC;
		callback : out STD_LOGIC := '0';
		EXTC : out STD_LOGIC := 'Z'
	);
end slower;

architecture arch of slower is

-- delay_val is (x * 2048 * 2) / 48_000_000
-- EXT_CLK = 4475 (~382 ms)
-- EXT+3 = 110 (~9.4 ms)
constant delay_val : integer := 110;
signal cnt : integer range 0 to delay_val := 0;
signal slow : STD_LOGIC := '0';

begin

process (CLK) is
begin
	if (rising_edge(CLK)) then
		if (in_slow = '1') then
			if (cnt < delay_val) then
				cnt <= cnt + 1;
				slow <= '0';
			else
				slow <= '1';
			end if;
		else
			slow <= '0';
			cnt <= 0;
		end if;
	end if;
end process;

process (slow) is
begin
	EXTC <= slow;
	callback <= slow;
end process;

end arch;
