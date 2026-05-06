// 使用 Hardhat 或 Truffle 部署
const hre = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);

  // 部署 OpenOracleToken
  const Token = await ethers.getContractFactory("OpenOracleToken");
  const token = await Token.deploy();
  await token.deployed();
  console.log("OpenOracleToken deployed to:", token.address);

  // 部署 OpenOracleVerification
  const Verification = await ethers.getContractFactory("OpenOracleVerification");
  const verification = await Verification.deploy();
  await verification.deployed();
  console.log("OpenOracleVerification deployed to:", verification.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });