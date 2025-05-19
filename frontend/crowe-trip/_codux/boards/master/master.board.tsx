import Master  from '../../../src/components/master/master';
import { ContentSlot, createBoard } from '@wixc3/react-board';
import { ComponentWrapper } from '_codux/wrappers/component-wrapper';

export default createBoard({
    name: 'Master',
    Board: () => (
        <ComponentWrapper>
            <ContentSlot>
                <Master />
            </ContentSlot>
        </ComponentWrapper>
    ),
});
