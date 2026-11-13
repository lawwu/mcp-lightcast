# Lightcast labor-market intelligence

This project connects MCP callers to licensed Lightcast data and combines related
lookups without inventing missing results.

## Language

**Lightcast account**:
The upstream account whose permissions and quotas govern a Lightcast request.
It is distinct from the identity of the caller connecting to the MCP server.

**Credential pair**:
A Lightcast client ID and client secret used to obtain tokens for permitted scopes.
Rotating the secret changes the credential pair without changing the account.

**Composed workflow**:
A sequence of Lightcast operations that answers one question while retaining the
meaning and provenance of the contributing results.

**Occupation inference**:
Finding skills associated with occupations identified from a normalized title.
These skills need not appear in the original title or description.
_Avoid_: Text extraction

**Explicit skill extraction**:
Identifying skills actually mentioned in supplied text, with extraction confidence.
It does not infer the skills associated with an occupation.
_Avoid_: Occupation inference

**Partial result**:
A workflow result containing successful earlier work and an explicit indication
that an optional downstream stage failed; it is not a complete skill profile.
