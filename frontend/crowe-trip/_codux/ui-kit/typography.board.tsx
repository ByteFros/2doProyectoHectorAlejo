import '../../src/styles/utils.scss';
import { createBoard, Variant } from '@wixc3/react-board';
import { Kit } from '../ui-kit-utils/kit';

export default createBoard({
    name: 'Typography',
    Board: () => (
        <Kit category="Foundation" title="Typography">
            <Kit.Section title="Heading">
                <Kit.Item>
                    <Variant name="Large Font">
                        <h1 className="largeFont">Large Font</h1>
                    </Variant>
                    <Kit.Description>
                        <b>--large-font:</b> DM Sans / 8vw / 1.2
                    </Kit.Description>
                </Kit.Item>
                <Kit.Item>
                    <Variant name="Small Font">
                        <h2 className="small-font">Small Font</h2>
                    </Variant>
                    <Kit.Description>
                        <b>--small-font:</b> DM Sans / 5vw / 1.4
                    </Kit.Description>
                </Kit.Item>
            </Kit.Section>

            <Kit.Section title="Paragraph">
                <Kit.Item>
                    <Variant name=" Paragraph Font">
                        <div className="paragraph-font">
                            We ignite opportunity by setting the world in motion. 0123456789
                        </div>
                    </Variant>
                    <Kit.Description>
                        <b>--paragraph-font:</b> DM Sans / 3vw / 1.3
                    </Kit.Description>
                </Kit.Item>
            </Kit.Section>
        </Kit>
    ),
    environmentProps: {
        windowWidth: 450,
        windowHeight: 700,
    },
    isSnippet: true,
});
