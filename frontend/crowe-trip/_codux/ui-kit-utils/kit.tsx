import classNames from 'classnames';
import { ReactNode } from 'react';
import styles from './kit.module.scss';

interface KitProps {
    category: string;
    title: string;
    children?: ReactNode;
    className?: string;
}

export const Kit = ({ category, title, children, className }: KitProps) => {
    return (
        <div className={classNames(styles.container, className)}>
            <div className={styles.header}>
                <b>UI Kit</b> | {category}
            </div>
            <h3 className={styles.title}>{title}</h3>
            {children}
        </div>
    );
};

interface SectionProps {
    title?: string;
    children?: ReactNode;
    className?: string;
}

const Section = ({ title, children, className }: SectionProps) => (
    <div className={classNames(styles.section, className)}>
        {title && <div className={styles.sectionTitle}>{title}</div>}
        {children}
    </div>
);

interface ItemProps {
    children?: ReactNode;
    className?: string;
}

const Item = ({ children, className }: ItemProps) => (
    <div className={classNames(styles.item, className)}>{children}</div>
);

const Description = ({ children }: { children?: ReactNode }) => (
    <div className={styles.itemDescription}>{children}</div>
);

Kit.Section = Section;
Kit.Item = Item;
Kit.Description = Description;
