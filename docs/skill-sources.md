# Skill provenance

The workflow was informed by michaelshimeles/skills at revision
513f8a24aae6383b00356fa285144b1bc3730dc1:
https://github.com/michaelshimeles/skills/tree/513f8a24aae6383b00356fa285144b1bc3730dc1

The three repository skills are newly written, project-specific instructions;
no upstream skill body, recorder, uploader, or other implementation is vendored.
They apply the ideas of isolated feature work, deliberate architecture, and
behavioral evidence to this FastAPI repository.

We do not adopt upstream's mandatory Greptile score loop, automatic public
screenshot uploads, or its blanket rule against services coordinating database
state. Those choices would add dependencies or conflict with our transaction model.
The upstream before-and-after tool has a separate PolyForm Shield license and is
not included. Reassess licensing and publishing behavior if it is added later.
