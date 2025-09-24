# Sample Documentation with Citations

## Valid Citations

The main trading logic is implemented in `codebase/daytrader/src/main/java/com/ibm/websphere/samples/daytrader/service/TradeService.java`.

Order processing happens in the [codebase/daytrader/src/main/java/com/ibm/websphere/samples/daytrader/service/OrderService.java] file.

Account management is handled by:
- file: codebase/daytrader/src/main/java/com/ibm/websphere/samples/daytrader/repository/AccountRepository.java
- location: "codebase/daytrader/src/main/java/com/ibm/websphere/samples/daytrader/validators/AccountValidator.java"

## Invalid Citations (these don't exist)

Some non-existent files that would trigger validation errors:
- `src/main/java/NonExistentController.java`
- [fake/path/to/InvalidService.java]
- "another/invalid/file.properties"

## Mixed Valid and Invalid

The `codebase/daytrader/src/main/java/com/ibm/websphere/samples/daytrader/web/TradeActionController.java` handles web requests (valid).

But this doesn't exist: `src/test/java/MissingTestFile.java` (invalid).