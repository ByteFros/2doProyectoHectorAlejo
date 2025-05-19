import { ChangePassword } from '../../../src/components/common/change-password/change-password';
import { ContentSlot, createBoard } from '@wixc3/react-board';
import { ComponentWrapper } from '_codux/wrappers/component-wrapper';

export default createBoard({
    name: 'ChangePassword',
    Board: () => (
        <ComponentWrapper>
            <ContentSlot>
                <ChangePassword />
            </ContentSlot>
        </ComponentWrapper>
    ),
});
