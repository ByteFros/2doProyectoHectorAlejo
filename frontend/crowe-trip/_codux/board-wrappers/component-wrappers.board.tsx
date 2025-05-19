import { ContentSlot, createBoard } from '@wixc3/react-board';
import { ComponentWrapper } from '_codux/wrappers/component-wrapper';

export default createBoard({
    name: 'NewBoard',
    Board: () => (
        <ComponentWrapper>
            <ContentSlot />
        </ComponentWrapper>
    ),
});
