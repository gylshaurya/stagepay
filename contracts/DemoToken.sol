// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/// @notice Free demonstration tokens. They have no cash value and anyone can mint them.
contract DemoToken is ERC20 {
    constructor() ERC20("Stagepay Demo Token", "DEMO") {
        // Only local Anvil and Ethereum Sepolia are supported for this demonstration.
        require(block.chainid == 31337 || block.chainid == 11155111, "test networks only");
    }
    function mint(address to, uint256 amount) external { _mint(to, amount); }
}
